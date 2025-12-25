from typing import Dict, List, Any, Union, Optional, Tuple, BinaryIO
from http.server import BaseHTTPRequestHandler, HTTPServer
import concurrent.futures
import requests
import joblib
import io
import pandas as pd
import json
import math
import webbrowser
import time
import threading
from urllib.parse import urlparse, parse_qs
import os

MAX_MODEL_SIZE_MB = 200
MAX_MODEL_SIZE = MAX_MODEL_SIZE_MB * 1024 * 1024

class MLServeError(Exception):
    """Custom exception for MLServeClient errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class MLServeClient:
    """Client for interacting with the MLServe API."""
    def __init__(self, server_url: str = "https://mlserve.com"):
        self.server_url = server_url
        self.token: Optional[str] = None

    def set_token(self, token: str) -> None:
        """Set the authentication token."""
        self.token = token

    def _headers(self) -> Dict[str, str]:
        """Generate headers with authentication token."""
        if not self.token:
            raise MLServeError("Authentication token missing. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None,
        auth_required: bool = True
    ) -> Dict:
        """Make an HTTP request to the MLServe API."""
        url = f"{self.server_url}{endpoint}"
        headers = self._headers() if auth_required else {}
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json_data,
                params=params,
                files=files
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            try:
                error_data = response.json()
                raise MLServeError(f"API request failed: {error_data.get('error', response.text)}", response.status_code)
            except ValueError:
                raise MLServeError(f"API request failed: {response.text}", response.status_code)
        except requests.RequestException as e:
            raise MLServeError(f"Request error: {str(e)}")

    @staticmethod
    def _sanitize_json(obj: Any) -> Any:
        """Recursively replace NaN/Inf with None for valid JSON serialization."""
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if isinstance(obj, list):
            return [MLServeClient._sanitize_json(item) for item in obj]
        if isinstance(obj, dict):
            return {key: MLServeClient._sanitize_json(value) for key, value in obj.items()}
        return obj

    def login(self, username: str, password: str) -> None:
        """Authenticate with the MLServe API and store the access token."""
        response = self._make_request(
            method="POST",
            endpoint="/api/v1/token",
            data={"username": username, "password": password},
            auth_required=False
        )
        self.token = response["access_token"]

    def deploy(
        self,
        model: Optional[Any] = None,
        requirements: Optional[str] = None,
        model_path: Optional[str] = None,
        requirements_path: Optional[str] = None,
        name: str = "model",
        version: str = "v1",
        features: Optional[List[str]] = None,
        background_df: Optional[pd.DataFrame] = None,
        metrics: Optional[Dict[str, float]] = None,
        task_type: Optional[str] = None
    ) -> Dict:
        """Deploy a model to the MLServe API."""
        if model is None and model_path is None:
            raise MLServeError("Either model or model_path must be provided.")

        files: Dict[str, Tuple[str, BinaryIO, str]] = {}
        if model is not None:
            model_bytes = io.BytesIO()
            joblib.dump(model, model_bytes)
            size = model_bytes.tell()  # current buffer position = total bytes
            size_mb = size / (1024 * 1024)
            if size > MAX_MODEL_SIZE:
                raise MLServeError(
                    f"Model too large ({size_mb:.1f} MB). Limit is {MAX_MODEL_SIZE_MB} MB."
                )
            model_bytes.seek(0)
            files["model_file"] = ("model.pkl", model_bytes, "application/octet-stream")
        else:
            # Read from disk and check size
            size = os.path.getsize(model_path)
            size_mb = size / (1024 * 1024)
            if size > MAX_MODEL_SIZE:
                raise MLServeError(
                    f"Model file too large ({size_mb:.1f} MB). Limit is {MAX_MODEL_SIZE_MB} MB."
                )
            with open(model_path, "rb") as f:
                files["model_file"] = ("model.pkl", f, "application/octet-stream")

        if requirements is not None:
            files["requirements_file"] = ("requirements.txt", io.BytesIO(requirements.encode()), "text/plain")
        elif requirements_path is not None:
            with open(requirements_path, "rb") as f:
                files["requirements_file"] = ("requirements.txt", f, "text/plain")

        form_data: Dict[str, str] = {"name": name, "version": version}
        if features is not None:
            if not isinstance(features, (list, tuple)) or not all(isinstance(f, str) for f in features):
                raise MLServeError("`features` must be a list of strings.")
            form_data["features"] = json.dumps(list(features))

        if background_df is not None:
            if not isinstance(background_df, pd.DataFrame):
                raise MLServeError("`background_df` must be a pandas DataFrame.")
            if features and set(background_df.columns) != set(features):
                raise MLServeError(f"Background DataFrame columns {list(background_df.columns)} do not match features {features}.")
            # Convert DataFrame to JSON
            form_data["background_data"] = background_df.to_json(orient="records", lines=False)
        
        if metrics is not None:
            form_data['metrics'] = json.dumps(metrics)
        
        if task_type is not None:
            form_data['task_type']=task_type

        return self._make_request(
            method="POST",
            endpoint="/api/v1/deploy",
            data=form_data,
            files=files
        )

    def stop_model(self, name: str, version: str, remove: bool = False) -> Dict:
        """Stop a deployed model version."""
        return self._make_request(
            method="POST",
            endpoint=f"/api/v1/stop/{name}/{version}",
            params={"remove":remove}
        )

    def start_model(self, name: str, version: str) -> Dict:
        """Start a deployed model version."""
        return self._make_request(
            method="POST",
            endpoint=f"/api/v1/start/{name}/{version}"
        )

    def predict(
        self,
        name: str,
        version: str,
        data: Dict[str, Any],
        explain: bool = False,
        fs_url: Optional[str] = None,
        fs_entity_name: Optional[str] = 'entity',
        materialize: bool = False,
    ) -> Dict:
        """
        Make predictions using a deployed model version.

        No client-side batching: sends request as-is.
        If materialize=True, backend stores predictions keyed by entity_id and returns an ACK payload.
        """
        clean_data = self._sanitize_json(data)

        if explain:
            clean_data["explain"] = True
        if fs_url:
            clean_data["fs_url"] = fs_url
        if fs_entity_name:
            clean_data["fs_entity_name"] = fs_entity_name
        if materialize:
            clean_data["materialize"] = True

        return self._make_request(
            method="POST",
            endpoint=f"/api/v1/predict/{name}/{version}",
            json_data=clean_data
        )


    def predict_weighted(
        self,
        name: str,
        data: Dict[str, Any],
        explain: bool = False,
        entity_ids: Optional[List[str]] = None,
        fs_url: Optional[str] = None,
        fs_entity_name: Optional[str] = 'entity',
        materialize: bool = False,
    ) -> Dict:
        """
        Make weighted predictions across model versions using A/B test weights.

        No client-side batching: sends request as-is.
        If materialize=True, backend stores predictions keyed by entity_id and returns an ACK payload.
        """
        clean_data = self._sanitize_json(data)

        if explain:
            clean_data["explain"] = True
        if fs_url:
            clean_data["fs_url"] = fs_url
        if fs_entity_name:
            clean_data["fs_entity_name"] = fs_entity_name
        if materialize:
            clean_data["materialize"] = True

        inputs = clean_data.get("inputs", [])

        # Optional entity_ids validation + attach
        if entity_ids is not None:
            if len(entity_ids) != len(inputs):
                raise ValueError(
                    f"Length of entity_ids ({len(entity_ids)}) must match length of inputs ({len(inputs)})"
                )
            clean_data["entity_ids"] = entity_ids

        return self._make_request(
            method="POST",
            endpoint=f"/api/v1/predict/{name}",
            json_data=clean_data
        )

    def fetch_materialized(
        self,
        name: str,
        entity_id: str,
        max_age_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetch a materialized prediction by entity_id.

        Backend endpoint:
          GET /api/v1/fetch-materialized/{name}?entity_id=...&max_age_seconds=...
        """
        params: Dict[str, Any] = {"entity_id": entity_id}
        if max_age_seconds is not None:
            params["max_age_seconds"] = max_age_seconds

        return self._make_request(
            method="GET",
            endpoint=f"/api/v1/fetch-materialized/{name}",
            params=params
        )

    # def predict(
    #     self,
    #     name: str,
    #     version: str,
    #     data: Dict[str, Any],
    #     explain: bool = False,
    #     batch_size: int = 500,
    #     parallel: int = 2,
    #     fs_url: Optional[str] = None,
    #     fs_entity_name: Optional[str] = 'entity'
    # ) -> Dict:
    #     """
    #     Make predictions using a deployed model version.
    #     Supports batching, parallel execution, and optional feature store lookup.
    #     If fs_url is provided, 'inputs' must be entity_ids, and backend
    #     will fetch features from Redis.
    #     """
    #     clean_data = self._sanitize_json(data)
    #     if explain:
    #         clean_data["explain"] = True
    #     if fs_url:
    #         clean_data["fs_url"] = fs_url
    #     if fs_entity_name:
    #         clean_data["fs_entity_name"]=fs_entity_name

    #     inputs = clean_data.get("inputs", [])

    #     # If no batching needed
    #     if not inputs or len(inputs) <= batch_size:
    #         return self._make_request(
    #             method="POST",
    #             endpoint=f"/api/v1/predict/{name}/{version}",
    #             json_data=clean_data
    #         )

    #     # Split inputs into batches
    #     num_batches = math.ceil(len(inputs) / batch_size)
    #     batches = [
    #         inputs[i * batch_size : (i + 1) * batch_size]
    #         for i in range(num_batches)
    #     ]

    #     # Precompute base data without inputs
    #     base_data = {k: v for k, v in clean_data.items() if k != "inputs"}

    #     def call_predict(batch_inputs):
    #         batch_data = dict(base_data)
    #         batch_data["inputs"] = batch_inputs
    #         return self._make_request(
    #             method="POST",
    #             endpoint=f"/api/v1/predict/{name}/{version}",
    #             json_data=batch_data
    #         )

    #     results = {"predictions": [], "explanations": [], "prediction_ids": []}

    #     with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
    #         for batch_result in executor.map(call_predict, batches):
    #             results["predictions"].extend(batch_result.get("predictions", []))
    #             results["explanations"].extend(batch_result.get("explanations", []))
    #             results["prediction_ids"].extend(batch_result.get("prediction_ids", []))

    #     return results

    # def predict_weighted(
    #     self,
    #     name: str,
    #     data: Dict[str, Any],
    #     explain: bool = False,
    #     entity_ids: Optional[List[str]] = None,
    #     batch_size: int = 500,
    #     parallel: int = 2,
    #     fs_url: Optional[str] = None,
    #     fs_entity_name: Optional[str] = 'entity'
    # ) -> Dict:
    #     """
    #     Make weighted predictions across model versions using A/B test weights.
    #     Supports batching, parallel execution, and optional feature store lookup.
    #     If fs_url is provided, 'inputs' must be entity_ids, and backend
    #     will fetch features from Redis.
    #     """
    #     clean_data = self._sanitize_json(data)
    #     if explain:
    #         clean_data["explain"] = True
    #     if fs_url:
    #         clean_data["fs_url"] = fs_url
    #     if fs_entity_name:
    #         clean_data["fs_entity_name"]=fs_entity_name

    #     inputs = clean_data.get("inputs", [])

    #     # Optional entity_ids validation
    #     if entity_ids is not None:
    #         if len(entity_ids) != len(inputs):
    #             raise ValueError("Length of entity_ids must match length of inputs")
    #         clean_data["entity_ids"] = entity_ids

    #     # If no batching needed
    #     if not inputs or len(inputs) <= batch_size:
    #         return self._make_request(
    #             method="POST",
    #             endpoint=f"/api/v1/predict/{name}",
    #             json_data=clean_data
    #         )

    #     # Split into batches
    #     num_batches = math.ceil(len(inputs) / batch_size)
    #     input_batches = [
    #         inputs[i * batch_size : (i + 1) * batch_size]
    #         for i in range(num_batches)
    #     ]
    #     entity_batches = (
    #         [
    #             entity_ids[i * batch_size : (i + 1) * batch_size]
    #             for i in range(num_batches)
    #         ]
    #         if entity_ids is not None
    #         else [None] * num_batches
    #     )

    #     # Precompute base data without inputs/entity_ids
    #     base_data = {k: v for k, v in clean_data.items() if k not in ("inputs", "entity_ids")}

    #     def call_predict(batch_inputs, batch_entities):
    #         batch_data = dict(base_data)
    #         batch_data["inputs"] = batch_inputs
    #         if batch_entities is not None:
    #             batch_data["entity_ids"] = batch_entities
    #         return self._make_request(
    #             method="POST",
    #             endpoint=f"/api/v1/predict/{name}",
    #             json_data=batch_data
    #         )

    #     results = {"predictions": [], "explanations": [], "prediction_ids": []}

    #     with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
    #         futures = [
    #             executor.submit(call_predict, batch_inputs, batch_entities)
    #             for batch_inputs, batch_entities in zip(input_batches, entity_batches)
    #         ]
    #         for future in concurrent.futures.as_completed(futures):
    #             batch_result = future.result()
    #             results["predictions"].extend(batch_result.get("predictions", []))
    #             results["explanations"].extend(batch_result.get("explanations", []))
    #             results["prediction_ids"].extend(batch_result.get("prediction_ids", []))

    #     return results

    def configure_abtest(self, name: str, weights: Dict[str, float]) -> Dict:
        """Configure A/B test weights for model versions."""
        return self._make_request(
            method="POST",
            endpoint=f"/api/v1/abtest/{name}",
            json_data=weights
        )

    def get_abtests(self, name: str) -> List[Dict]:
        """Get the list of A/B test configurations for a model."""
        return self._make_request(method="GET", endpoint=f"/api/v1/abtest/{name}")

    def list_models(self) -> List[Dict]:
        """List all deployed models and their versions."""
        return self._make_request(method="GET", endpoint="/api/v1/models")

    def get_latest_version(self, model_name: str) -> Dict:
        """
        Get the latest deployed version of a model and the suggested next version.

        Args:
            model_name (str): The name of the model.

        Returns:
            Dict: Dictionary with latest version info and next_version.
        """
        endpoint = f"/api/v1/models/{model_name}/latest"
        return self._make_request(method="GET", endpoint=endpoint)

    def send_feedback(self, items: List[Dict[str, Any]]) -> Dict:
        """
        items = [{"prediction_id": "...", "true_value": 1, "reward": 12.3, "metadata": {...}}, ...]
        """
        payload = {"feedback": items}
        return self._make_request(method="POST", endpoint="/api/v1/feedback", json_data=payload)

    def get_online_metrics(self, name: str, version: str, window_hours: int = 168, as_dataframe: bool = False) -> Union[Dict, pd.DataFrame]:
        """
        Retrieve online performance metrics for a model - version).
        Returns a single-row pandas DataFrame with unpacked metrics.
        """
        params = {"version": version, "window_hours": window_hours} if version else {"window_hours": window_hours}
        resp = self._make_request(
            method="GET",
            endpoint=f"/api/v1/metrics/{name}/online",
            params=params
        )

        if "metrics" not in resp:
            if as_dataframe:
                return pd.DataFrame()
            else:
                return {}

        row = {
            "model": name,
            "version": resp.get("version"),
            "window_hours": resp.get("window_hours"),
            "n": resp.get("n"),
            "n_supervised": resp.get("n_supervised"),
        }
        row.update(resp.get("metrics", {}))

        if as_dataframe:
            return pd.DataFrame([row])
        else:
            return row

    def get_model_evolution(self, name: str, as_dataframe: bool = False) -> Union[Dict, pd.DataFrame]:
        """
        Retrieve model evolution metrics across versions and return as a pandas DataFrame.
        Unpacks metrics + deltas for easy analysis.
        """
        resp = self._make_request(
            method="GET",
            endpoint=f"/api/v1/models/{name}/evolution"
        )

        versions = resp.get("versions", [])
        if not versions:
            return pd.DataFrame()

        # Flatten metrics + deltas
        rows = []
        for v in versions:
            base = {
                "version": v.get("version"),
                "deployed_at": v.get("deployed_at")
            }
            base.update(v.get("metrics", {}))
            base.update(v.get("deltas", {}))  # optional, may not exist for v1
            rows.append(base)

        if as_dataframe:
            df = pd.DataFrame(rows)
            df = df.sort_values(by="deployed_at").reset_index(drop=True)
            return df
        return rows

    def get_metrics(self, name: str, version: str, hours: int = 24, as_dataframe: bool = False) -> Union[Dict, pd.DataFrame]:
        """Fetch hourly metrics for a model version."""
        response = self._make_request(
            method="GET",
            endpoint=f"/api/v1/metrics/{name}/{version}",
            params={"hours": hours}
        )
        if as_dataframe:
            series = response.get("timeseries", [])
            if not series:
                return pd.DataFrame()
            df = pd.DataFrame(series)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.set_index("timestamp").sort_index()
            return df
        return response

    def get_data_quality(self, name: str, version: str, hours: int = 24, as_dataframe: bool = False) -> Union[Dict, Dict[str, pd.DataFrame]]:
        """Fetch data quality metrics for a model version."""
        response = self._make_request(
            method="GET",
            endpoint=f"/api/v1/data-quality-agg/{name}/{version}",
            params={"hours": hours}
        )
        if as_dataframe and "message" not in response:
            return {
                "missingness": pd.DataFrame(response.get("missingness", [])),
                "drift": pd.DataFrame(response.get("drift", [])),
                "outliers": pd.DataFrame(response.get("outliers", []))
            }
        return response

    def get_user_tier(self) -> str:
        """Get the current user's tier."""
        response = self._make_request(method="GET", endpoint="/api/v1/user_tier")
        return response["tier"]

    def get_user_role(self) -> str:
        """Get the current user's role."""
        response = self._make_request(method="GET", endpoint="/api/v1/user_role")
        return response["role"]

    def register(self, user_name: str, email: str, password: str) -> Dict:
        """
        Register a new user account.

        This method calls the /api/v1/register endpoint. The backend will:
        - Create a new user and organization (client).
        - Send a verification email with a confirmation link.
        - The user must verify the account via the email before logging in.

        Args:
            user_name (str): Display name or full name of the user.
            email (str): Email address for the account.
            password (str): Desired password for the account.

        Returns:
            Dict: API response message (e.g. {"message": "Account created successfully! Please check your email to verify your account."})
        """
        if not user_name:
            raise MLServeError("A user name is required to register.")
        if not email or "@" not in email:
            raise MLServeError("A valid email address is required to register.")
        if not password or len(password) < 6:
            raise MLServeError("Password must be at least 6 characters long.")

        payload = {
            "full_name": user_name,
            "email": email,
            "password": password
        }

        return self._make_request(
            method="POST",
            endpoint="/api/v1/register",
            json_data=payload,
            auth_required=False
        )

    def google_login(self):
        """
        Trigger Google OAuth login using the API.
        Opens a browser for authentication. After login, the backend returns
        the JWT directly, which is stored in `self.token`.
        """
        # Step 1: Get Google auth URL from backend
        auth_info = self._make_request("GET", "/api/v1/auth/google", auth_required=False)
        auth_url = auth_info.get("auth_url")
        if not auth_url:
            raise MLServeError("Failed to get Google login URL from server.")

        print("🌐 Opening Google login page in your browser...")
        webbrowser.open(auth_url)

        print("ℹ️ After completing login in the browser, copy the full response and paste it here.")
        token_resp = input("Paste the full response that was returned: ").strip()

        try:
            token_resp = json.loads(token_resp)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")

        access_token = token_resp.get("access_token")
        if not access_token:
            raise MLServeError("Failed to retrieve access token from server.")

        self.token = access_token
        print(f"✅ Google login successful! Logged in as {token_resp.get('email')}")

    def invite(self, email: str) -> Dict:
        """
        Invite a new user by email.

        This method calls the /api/v1/invite/ endpoint. The backend will:
        - Generate a verification token tied to the invitee email.
        - Send an invitation email with a verification link.
        - Return a confirmation message.

        Args:
            email (str): Email address of the user to invite.

        Returns:
            Dict: API response (e.g. {"detail": "Invite sent to user@example.com. Check your email."})
        """
        if not email or "@" not in email:
            raise MLServeError("A valid email address is required.")

        payload = {"email": email}

        return self._make_request(
            method="POST",
            endpoint="/api/v1/invite/",
            json_data=payload
        )

    def request_password_reset(self, email: str, new_password: str) -> Dict:
        """
        Request a password reset email for an existing user.

        This method calls the /api/v1/password-reset-request/ endpoint.
        The backend will:
        - Verify that the user exists.
        - Generate a temporary access token.
        - Send a password reset email with a verification link.

        Args:
            email (str): The email address of the user requesting the reset.

        Returns:
            Dict: API response (e.g. {"message": "Please check your email for instructions to reset your password"})
        """
        if not email or "@" not in email:
            raise MLServeError("A valid email address is required to request a password reset.")

        payload = {"email": email, "new_password":new_password}

        return self._make_request(
            method="POST",
            endpoint="/api/v1/password-reset-request/",
            json_data=payload,
            auth_required=False
        )

    # ---------------------------------------------------------
    # 👥 TEAM MANAGEMENT
    # ---------------------------------------------------------

    def list_team_members(self) -> List[Dict]:
        """
        List all team members (users) under the same client/organization.

        Returns:
            List[Dict]: List of team members with user_id, email, name, role, etc.
        """
        return self._make_request(
            method="GET",
            endpoint="/api/v1/team/"
        )

    def update_user_role(self, user_id: int, new_role: str) -> Dict:
        """
        Update a user's role within the same organization.
        Only superadmin/admin can perform this.

        Args:
            user_id (int): ID of the target user.
            new_role (str): One of ['admin', 'user'].

        Returns:
            Dict: Confirmation message.
        """
        payload = {"role": new_role}
        return self._make_request(
            method="PUT",
            endpoint=f"/api/v1/team/{user_id}/role",
            json_data=payload
        )

    def remove_team_member(self, user_id: int) -> Dict:
        """
        Remove a user (soft delete / disable account).

        Args:
            user_id (int): ID of the user to remove.

        Returns:
            Dict: Confirmation message.
        """
        return self._make_request(
            method="DELETE",
            endpoint=f"/api/v1/team/{user_id}/remove"
        )

    # =========================================================
    # 🤖 ONLINE (REINFORCEMENT LEARNING) METHODS
    # =========================================================

    def configure_online_model(
        self,
        name: str,
        version: str,
        task_type: str,
        feature_contract: Dict[str, Any]
    ) -> Dict:
        """
        Configure and deploy an online (reinforcement learning) model.

        Args:
            name (str): Model name.
            version (str): Version identifier.
            task_type (str): Task type (e.g., 'policy_next', 'bandit', etc.)
            feature_contract (Dict): JSON contract with 'features' and 'actions' keys, e.g.:

                {
                    "features": [
                        {"name": "age", "type": "continuous"},
                        {"name": "country", "type": "categorical", "values": ["US", "DE", "FR"]}
                    ],
                    "actions": ["show_discount", "show_premium", "no_action"]
                }

        Returns:
            Dict: Deployment result with URLs for predict and feedback.
        """
        form_data = {
            "name": name,
            "version": version,
            "task_type": task_type,
            "feature_contract": json.dumps(feature_contract)
        }

        return self._make_request(
            method="POST",
            endpoint="/api/v1/model_config",
            data=form_data
        )

    def online_predict(
        self,
        name: str,
        version: str,
        inputs: List[Dict[str, Any]]
    ) -> Dict:
        """
        Call an online (RL) model to select actions given context features.

        Args:
            name (str): Model name.
            version (str): Version identifier.
            inputs (List[Dict]): List of feature dictionaries (one per record).

        Example:
            client.online_predict(
                name="promo-policy",
                version="v1",
                inputs=[
                    {"age": 25, "country": "US"},
                    {"age": 42, "country": "DE"}
                ]
            )

        Returns:
            Dict with 'predictions' and 'prediction_ids'.
        """
        payload = {"inputs": inputs}
        return self._make_request(
            method="POST",
            endpoint=f"/api/v1/online_predict/{name}/{version}",
            json_data=payload
        )

    def online_feedback(
        self,
        name: str,
        version: str,
        feedback: List[Dict[str, Any]]
    ) -> Dict:
        """
        Send feedback (rewards) to an online RL model for training updates.

        Args:
            name (str): Model name.
            version (str): Version identifier.
            feedback (List[Dict]): List of feedback records with structure:

                [
                    {
                        "features": {...},          # same structure as used in predict
                        "action": "show_discount",  # or int index
                        "reward": 0.8,
                        "policy_id": 0,
                        "metadata": {"session_id": "..."}
                    },
                    ...
                ]

        Returns:
            Dict with summary info, avg reward, and worker response.
        """
        payload = {"feedback": feedback}
        return self._make_request(
            method="POST",
            endpoint=f"/api/v1/online_feedback/{name}/{version}",
            json_data=payload
        )

    def get_rl_metrics(
        self,
        name: str,
        version: str,
        window_hours: int = 168,
        granularity: str = "hour",
        as_dataframe: bool = False
    ) -> Union[Dict, pd.DataFrame]:
        """
        Retrieve reinforcement learning (RL) policy metrics for a deployed model.

        Calls the `/api/v1/metrics/rl/{model}/{version}` endpoint.

        Includes:
        - Aggregate epsilon, reward, and policy statistics
        - Per-policy reward stats (mean, median, std, n)
        - Time-bucketed reward & epsilon series
        - Per-policy reward series for trend analysis

        Parameters
        ----------
        name : str
            Model name (policy model identifier)
        version : str
            Model version
        window_hours : int, default=168
            Time window (in hours) for metric aggregation
        granularity : {'hour', 'day'}, default='hour'
            Time bucket granularity for time-series aggregation
        as_dataframe : bool, default=False
            If True, returns pandas DataFrames for each time series

        Returns
        -------
        dict or dict[str, pd.DataFrame]
            Dictionary containing summary metrics and time-bucketed series.
            If `as_dataframe=True`, returns:
            {
                "summary": pd.DataFrame([...]),
                "epsilon_series": pd.DataFrame([...]),
                "reward_series": pd.DataFrame([...]),
                "policy_series": pd.DataFrame([...]),
                "policy_reward_series": dict[int, pd.DataFrame]
            }
        """
        params = {
            "window_hours": window_hours,
            "granularity": granularity
        }

        resp = self._make_request(
            method="GET",
            endpoint=f"/api/v1/metrics/rl/{name}/{version}",
            params=params
        )

        # No data case
        if "metrics" not in resp:
            if as_dataframe:
                return {
                    "summary": pd.DataFrame(),
                    "epsilon_series": pd.DataFrame(),
                    "reward_series": pd.DataFrame(),
                    "policy_series": pd.DataFrame(),
                    "policy_reward_series": {}
                }
            else:
                return {}

        # --- Summary metrics ---
        summary = {
            "model": resp.get("model"),
            "version": resp.get("version"),
            "window_hours": resp.get("window_hours"),
            "granularity": resp.get("granularity"),
            "n_predictions": resp.get("n_predictions"),
            "n_feedback": resp.get("n_feedback"),
            **resp.get("metrics", {})
        }

        if not as_dataframe:
            return resp

        # --- Convert to DataFrames for analysis ---
        series = resp.get("series", {})
        epsilon_series = pd.DataFrame(series.get("epsilon", []))
        reward_series = pd.DataFrame(series.get("reward", []))
        policy_series = pd.DataFrame(series.get("policy_selection", []))

        # Per-policy reward time series (list of dicts → {policy_id: df})
        policy_reward_series_dict = {}
        for pr in series.get("policy_rewards", []):
            pid = pr.get("policy_id")
            df = pd.DataFrame(pr.get("series", []))
            if not df.empty:
                df["policy_id"] = pid
            policy_reward_series_dict[pid] = df

        summary_df = pd.DataFrame([summary])

        return {
            "summary": summary_df,
            "epsilon_series": epsilon_series,
            "reward_series": reward_series,
            "policy_series": policy_series,
            "policy_reward_series": policy_reward_series_dict
        }


    # =========================================================
    # 🚀 DEPLOYMENT MANAGEMENT
    # =========================================================

    def list_deployments(self) -> List[Dict[str, Any]]:
        """
        List all model deployments for the current user.

        Returns:
            List[Dict]: List of deployments with id, model_name, version, status, and timestamps.
        """
        return self._make_request(
            method="GET",
            endpoint="/api/v1/deployments"
        )

    def get_deployment_status(self, deployment_id: int) -> Dict[str, Any]:
        """
        Get the current status of a specific deployment.

        Args:
            deployment_id (int): The deployment ID returned when configuring or deploying a model.

        Returns:
            Dict: Deployment info including status ('pending', 'building', 'success', 'failed') and logs if available.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/api/v1/deployments/{deployment_id}"
        )

    def wait_for_deployment(
        self,
        deployment_id: int,
        poll_interval: int = 5,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Poll deployment status until completion or timeout.

        Args:
            deployment_id (int): The ID of the deployment to monitor.
            poll_interval (int): Seconds between checks (default 5s).
            timeout (int): Maximum time in seconds to wait (default 600s = 10 min).

        Returns:
            Dict: Final deployment status info.
        Raises:
            MLServeError: If deployment fails or times out.
        """
        start_time = time.time()
        while True:
            status_info = self.get_deployment_status(deployment_id)
            status = status_info.get("status")

            if status in ("success", "failed"):
                return status_info

            if time.time() - start_time > timeout:
                raise MLServeError(f"Deployment {deployment_id} timed out after {timeout} seconds")

            print(f"⏳ Deployment {deployment_id} status: {status or 'pending'}...")
            time.sleep(poll_interval)

    # =========================================================
    # 📉 CHURN APPS
    # =========================================================

    def churn_analysis(
        self,
        csv_file: Union[str, BinaryIO],
        max_discount_fraction: float = 0.2,
    ) -> Dict:
        """
        Run churn analysis for the current client.

        - Accepts a CSV file path or a file-like object (e.g. Streamlit UploadedFile).
        - Sends it to /api/v1/churn/analysis.
        - Returns the backend JSON (summary + customers).

        Args:
            csv_file: Path to CSV file or a file-like object with .read() / .getvalue().
            max_discount_fraction: Max fraction of total spend the model can suggest
                                   as a discount (e.g. 0.2 = 20%).

        Returns:
            Dict: {"message": "...", "summary": {...}, "customers": [...]}
        """
        # Read file contents and infer filename
        if isinstance(csv_file, str):
            filename = os.path.basename(csv_file) or "data.csv"
            with open(csv_file, "rb") as f:
                content = f.read()
        else:
            # File-like object (e.g. Streamlit UploadedFile)
            filename = getattr(csv_file, "name", "data.csv")
            try:
                content = csv_file.getvalue()
            except AttributeError:
                content = csv_file.read()

        file_obj = io.BytesIO(content)
        files = {
            "csv_file": (filename, file_obj, "text/csv"),
        }

        data = {
            "max_discount_fraction": str(max_discount_fraction),
        }

        return self._make_request(
            method="POST",
            endpoint="/api/v1/churn/analysis",
            data=data,
            files=files,
        )

    def churn_insights(self, limit: Optional[int] = None) -> Dict:
        """
        Fetch the latest churn analysis insights for the current client.

        Args:
            limit: Optional limit on number of customer rows returned.

        Returns:
            Dict: {
                "has_results": bool,
                "summary": {...} or None,
                "customers": [...]
            }
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit

        return self._make_request(
            method="GET",
            endpoint="/api/v1/churn/insights",
            params=params,
        )
