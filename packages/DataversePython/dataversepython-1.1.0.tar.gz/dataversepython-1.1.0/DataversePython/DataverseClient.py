import logging, os, requests, json
import pandas as pd
from typing import Literal, List
from .auth import MSALInteractiveAuth, MSALClientSecretAuth, AuthenticationProvider
from .api_client import ApiClient, BatchOperation

class DataverseClient:
    def __init__(
        self,
        config_json: str,
        auth_method: Literal["interactive", "client_secret"] = "interactive",
        log_level: int | str | None = None,
    ):
        """
        Initialize the Dataverse client with authentication.
        
        Args:
            config_json (str): Path to JSON configuration file.
            auth_method (Literal["interactive", "client_secret"]): Authentication method to use.
                - "interactive": MSAL public client flow with browser prompt (requires user sign-in).
                - "client_secret": MSAL confidential client flow using a client secret (no user interaction).
              Defaults to "interactive".
        
        Raises:
            ValueError: If an invalid auth_method is provided.
        """
        self.config_json = config_json
        workingDirectory = os.getcwd()
        
        self.logger = logging.getLogger(__name__)
        # Resolve desired log level (default to DEBUG to preserve current behavior)
        selected_level = self._resolve_log_level(log_level) if log_level is not None else logging.DEBUG
        self.logger.setLevel(selected_level)
        if not self.logger.handlers:
            file_handler = logging.FileHandler(os.path.join(workingDirectory, 'DataverseClient.log'))
            file_handler.setLevel(selected_level)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        else:
            # Ensure all existing handlers align with selected level
            for h in self.logger.handlers:
                h.setLevel(selected_level)
        
        # Select authentication provider based on auth_method
        auth_provider = self._get_auth_provider(auth_method)
        
        # Load config and authenticate
        config = json.load(open(config_json))
        authentication = auth_provider.authenticate(config)
        self.session: requests.Session = authentication[0]
        self.environmentURI: str = authentication[1]
        
        # Initialize shared API client for unified HTTP handling
        self.api = ApiClient(self.session, self.environmentURI, self.logger)

    def _resolve_log_level(self, level: int | str) -> int:
        """
        Resolve a logging level provided as int or common string name.

        Supported strings: 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'
        """
        if isinstance(level, int):
            return level
        if isinstance(level, str):
            name = level.strip().upper()
            mapping = {
                'CRITICAL': logging.CRITICAL,
                'ERROR': logging.ERROR,
                'WARNING': logging.WARNING,
                'INFO': logging.INFO,
                'DEBUG': logging.DEBUG,
                'NOTSET': logging.NOTSET,
            }
            if name in mapping:
                return mapping[name]
        raise ValueError(f"Invalid log level: {level}. Use int or one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET.")

    def set_log_level(self, level: int | str) -> None:
        """
        Change the logger level at runtime for this client and all its handlers.

        Examples:
            client.set_log_level('INFO')
            client.set_log_level(logging.ERROR)
        """
        resolved = self._resolve_log_level(level)
        self.logger.setLevel(resolved)
        for h in self.logger.handlers:
            h.setLevel(resolved)
        # Optional info entry to confirm change
        self.logger.info(f"Log level set to {logging.getLevelName(resolved)}")
    
    def _get_auth_provider(
        self, auth_method: Literal["interactive", "client_secret"]
    ) -> AuthenticationProvider:
        """
        Get the appropriate authentication provider based on the auth_method.
        
        Args:
            auth_method (Literal["interactive", "client_secret"]): The authentication method name.
        
        Returns:
            AuthenticationProvider: An instance of the appropriate authentication provider.
        
        Raises:
            ValueError: If an invalid auth_method is provided.
        """
        auth_providers = {
            "interactive": MSALInteractiveAuth(),
            "client_secret": MSALClientSecretAuth()
        }
        
        if auth_method not in auth_providers:
            raise ValueError(
                f"Invalid auth_method: '{auth_method}'. "
                f"Valid options are: {', '.join(auth_providers.keys())}"
            )
        
        return auth_providers[auth_method]


        
    def get_rows(self, entity: str, top: int | None = None, columns: list = [], filter: str | None = None, include_odata_annotations: bool = False) -> pd.DataFrame:
        """
        Retrieves rows from a specified Dataverse entity and returns them as a pandas DataFrame.
        Args:
            entity (str): The logical name of the Dataverse entity to query. Use PLURAL form (e.g. accounts, contacts).
            top (int, optional): The maximum number of rows to retrieve. If None, retrieves all available rows.
            columns (list, optional): List of column names to select. If empty, all columns are retrieved.
            filter (str, optional): OData filter string to apply to the query. If None, no filter is applied.
            include_odata_annotations (bool, optional): If True, includes OData annotations in the response. When using columns, odata annotations are also filtered.
        Returns:
            pd.DataFrame: A DataFrame containing the retrieved rows from the specified entity.
        Raises:
            Exception: If the HTTP request to the Dataverse API fails.
        """
        get_headers = self.session.headers.copy()
        if include_odata_annotations:
            get_headers.update({'Prefer': 'odata.include-annotations=*'})

        path = f'api/data/v9.2/{entity}'
        params: dict[str, str] = {}
        if top:
            params['$top'] = str(top)
        if columns:
            params['$select'] = ','.join(columns)
        if filter:
            params['$filter'] = filter

        rows = self.api.get_paginated(path, params=params, headers=get_headers)
        df = pd.DataFrame(rows)
        self.logger.info(f"Retrieved {len(df)} rows from entity '{entity}'.")
        return df
        
    def insert_rows(self, entity: str, df: pd.DataFrame, batch_size: int = 100) -> None:
        """
        Inserts rows from a pandas DataFrame into a specified Dataverse entity.
        
        Args:
            entity (str): The logical name of the Dataverse entity to insert rows into. Use PLURAL form (e.g. accounts, contacts).
            df (pd.DataFrame): The DataFrame containing the rows to be inserted. Each row should match the entity's schema.
            batch_size (int, optional): Number of rows to include per batch request. Default is 100.
                Maximum value is 1000 (Dataverse API limit). Smaller batches reduce memory usage but increase request count.
        
        Notes:
            - When batch_size < total rows, multiple batch requests are sent automatically.
            - Each batch is non-transactional (continue-on-error allows partial success).
            - The method logs summary statistics including success/failure counts and OData-EntityId for each created record.
            - On successful insertion (status code 201), the OData-EntityId is extracted and logged.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if batch_size > 1000:
            batch_size = 1000
            self.logger.warning(f"batch_size clamped to 1000 (Dataverse API limit)")

        insert_headers = dict(self.session.headers)
        insert_headers.update({'Content-Type': 'application/json; charset=utf-8'})

        path = f'api/data/v9.2/{entity}'
        total_rows = len(df)
        batch_num = 0
        
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            batch_num += 1
            
            operations = []
            for content_id, (idx, row) in enumerate(batch_df.iterrows(), start=1):
                payload = json.loads(row.to_json())
                operations.append(
                    BatchOperation(
                        method="POST",
                        path=f"/api/data/v9.2/{entity}",
                        json_body=payload,
                        content_id=content_id,
                        headers=None
                    )
                )
            
            # Send batch request (non-transactional; partial success allowed)
            resp, results = self.api.post_batch(
                operations=operations,
                use_changeset=False,
                continue_on_error=True
            )
            
            # Log per-operation results
            successful = 0
            failures = 0
            for result in results:
                row_index = batch_start + result.content_id - 1
                # Treat any 2xx status as success (Dataverse often returns 204 No Content on create)
                if 200 <= result.status_code < 300:
                    successful += 1
                    created_id = result.headers.get("OData-EntityId") or result.headers.get("Location")
                    if created_id:
                        self.logger.info(
                            f"Insert success entity={entity} row_index={row_index} "
                            f"status={result.status_code} created_id={created_id}"
                        )
                    else:
                        self.logger.info(
                            f"Insert success entity={entity} row_index={row_index} status={result.status_code}"
                        )
                else:
                    failures += 1
                    error_msg = result.error.get("message") if result.error else "Unknown error"
                    self.logger.error(
                        f"Insert failed entity={entity} row_index={row_index} "
                        f"status={result.status_code} error={error_msg}"
                    )
            
            self.logger.info(
                f"Insert batch complete entity={entity} batch={batch_num} "
                f"batch_size={len(operations)} success={successful} failures={failures}"
            )
    
    def upsert_rows(self, entity: str, df: pd.DataFrame, primary_key_col: str, only_update_if_exists: bool = False, batch_size: int = 100) -> None:
        """
        Upserts rows for a specified Dynamics 365 entity using data from a pandas DataFrame.
        
        This method batches rows and sends them as atomic PATCH requests to Dataverse.
        It updates existing records or creates new ones based on the primary key.
        
        Args:
            entity (str):
                The name of the Dynamics 365 entity to update. Use PLURAL form (e.g. accounts, contacts).
            df (pandas.DataFrame):
                DataFrame containing the rows to upsert. Must include a column representing the primary key.
            primary_key_col (str):
                The name of the DataFrame column that contains the unique identifier for each row.
            only_update_if_exists (bool, optional):
                If True, the function will only update existing records and will not create new ones.
                Defaults to False.
            batch_size (int, optional):
                Number of rows to include per batch request. Default is 100.
                Maximum value is 1000 (Dataverse API limit). Using changesets (atomicity) is recommended
                for smaller batches to ensure transactional safety.
        
        Notes:
            - Rows are batched and sent with changeset headers for atomic transactions (all-or-nothing per batch).
            - Each batch uses If-Match (all existing) or If-None-Match (allow new) headers based on only_update_if_exists.
            - Boolean strings ("true"/"false") are normalized to Python bool.
            - Null/NaN values are dropped from payloads before sending.
            - The method logs per-operation results and batch summary statistics.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if batch_size > 1000:
            batch_size = 1000
            self.logger.warning(f"batch_size clamped to 1000 (Dataverse API limit)")

        upsert_headers = dict(self.session.headers)
        if only_update_if_exists:
            upsert_headers.update({'If-Match': '*'})
        else:
            upsert_headers.update({'If-None-Match': '*'})

        path = f'api/data/v9.2/{entity}'
        total_rows = len(df)
        batch_num = 0
        total_success = 0
        total_failures = 0
        
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            batch_num += 1
            
            operations = []
            for content_id, (idx, row) in enumerate(batch_df.iterrows(), start=1):
                guid = row[primary_key_col]
                operation_path = f"/api/data/v9.2/{entity}({guid})"
                
                # Convert row to payload, excluding primary key
                payload = json.loads(batch_df.drop(columns=primary_key_col).iloc[content_id - 1].to_json())
                
                # Normalize booleans encoded as strings
                for key, value in list(payload.items()):
                    if isinstance(value, str):
                        lv = value.lower()
                        if lv == "false":
                            payload[key] = False
                        elif lv == "true":
                            payload[key] = True
                
                # Drop nulls and NaN values
                payload = {k: v for k, v in payload.items() if pd.notna(v)}
                
                operations.append(
                    BatchOperation(
                        method="PATCH",
                        path=operation_path,
                        json_body=payload,
                        content_id=content_id,
                        headers=None
                    )
                )
            
            # Send batch request (transactional with changeset)
            resp, results = self.api.post_batch(
                operations=operations,
                use_changeset=True,
                continue_on_error=False
            )
            
            # Log per-operation results
            batch_success = 0
            batch_failures = 0
            for result in results:
                row_index = batch_start + result.content_id - 1
                if result.status_code == 204:
                    batch_success += 1
                    total_success += 1
                    self.logger.debug(
                        f"Upsert success entity={entity} row_index={row_index} status={result.status_code}"
                    )
                else:
                    batch_failures += 1
                    total_failures += 1
                    error_msg = result.error.get("message") if result.error else "Unknown error"
                    self.logger.error(
                        f"Upsert failed entity={entity} row_index={row_index} "
                        f"status={result.status_code} error={error_msg}"
                    )
            
            self.logger.info(
                f"Upsert batch complete entity={entity} batch={batch_num} "
                f"batch_size={len(operations)} success={batch_success} failures={batch_failures}"
            )
        
        self.logger.info(
            f"Upsert summary entity={entity} total_success={total_success} "
            f"total_failures={total_failures} expected={total_rows}"
        )

    def delete_rows(self, entity: str, ids: List[str], batch_size: int = 100, use_changeset: bool = False, continue_on_error: bool = True) -> None:
        """
        Deletes rows from a specified Dataverse entity using a list of record IDs.
        
        Args:
            entity (str): The logical name of the Dataverse entity to delete from. Use PLURAL form (e.g. accounts, contacts).
            ids (List[str]): List of record IDs (GUIDs) to delete.
            batch_size (int, optional): Number of records to include per batch request. Default is 100.
                Maximum value is 1000 (Dataverse API limit).
            use_changeset (bool, optional): If True, wrap deletes in a changeset for atomicity (all-or-nothing per batch).
                If False (default), deletes are independent and continue on error is allowed. Defaults to False.
            continue_on_error (bool, optional): If True, one delete failure does not stop remaining deletes.
                Ignored if use_changeset=True. Defaults to True.
        
        Notes:
            - Per Microsoft Dataverse Web API docs, DELETE requires If-Match header (using '*' to bypass ETag check).
            - Batch delete operations may timeout with large batch_size; adjust as needed.
            - The method logs per-operation results and batch summary statistics.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if batch_size > 1000:
            batch_size = 1000
            self.logger.warning(f"batch_size clamped to 1000 (Dataverse API limit)")

        total_ids = len(ids)
        batch_num = 0
        total_success = 0
        total_failures = 0
        
        for batch_start in range(0, total_ids, batch_size):
            batch_end = min(batch_start + batch_size, total_ids)
            batch_ids = ids[batch_start:batch_end]
            batch_num += 1
            
            operations = []
            for content_id, record_id in enumerate(batch_ids, start=1):
                operation_path = f"/api/data/v9.2/{entity}({record_id})"
                operations.append(
                    BatchOperation(
                        method="DELETE",
                        path=operation_path,
                        json_body=None,
                        content_id=content_id,
                        # Per Microsoft docs, include If-Match: * to bypass ETag concurrency check
                        headers={"If-Match": "*"}
                    )
                )
            
            # Send batch request
            resp, results = self.api.post_batch(
                operations=operations,
                use_changeset=use_changeset,
                continue_on_error=continue_on_error
            )
            
            # Log per-operation results
            batch_success = 0
            batch_failures = 0
            for result in results:
                record_id = batch_ids[result.content_id - 1]
                if result.status_code == 204:
                    batch_success += 1
                    total_success += 1
                    self.logger.debug(
                        f"Delete success entity={entity} id={record_id} status={result.status_code}"
                    )
                else:
                    batch_failures += 1
                    total_failures += 1
                    error_msg = result.error.get("message") if result.error else "Unknown error"
                    self.logger.error(
                        f"Delete failed entity={entity} id={record_id} "
                        f"status={result.status_code} error={error_msg}"
                    )
            
            self.logger.info(
                f"Delete batch complete entity={entity} batch={batch_num} "
                f"batch_size={len(operations)} success={batch_success} failures={batch_failures}"
            )
        
        self.logger.info(
            f"Delete summary entity={entity} total_success={total_success} "
            f"total_failures={total_failures} total_ids={total_ids}"
        )

    def delete_row(self, entity: str, record_id: str, force: bool = True) -> None:
        """
        Delete a single row by GUID using the Dataverse Web API.

        Args:
            entity (str): Logical name of the entity (plural, e.g., "accounts").
            record_id (str): GUID of the record to delete.
            force (bool): If True, include If-Match: * to delete without ETag. Defaults to True.

        Notes:
            - Per Microsoft docs, DELETE requires either a matching ETag in If-Match or '*'.
            - Success returns HTTP 204 No Content.
        """
        headers = dict(self.session.headers)
        if force:
            headers.update({"If-Match": "*"})

        path = f"api/data/v9.2/{entity}({record_id})"
        resp = self.api.delete(path, headers=headers)

        if resp.status_code == 204:
            self.logger.info(f"Delete success entity={entity} id={record_id} status={resp.status_code}")
        else:
            content = resp.text
            self.logger.error(
                f"Delete failed entity={entity} id={record_id} status={resp.status_code} response={content}"
            )

    def insert_m_n(self, entity_m: str, entity_n: str, relationship_name: str, df: pd.DataFrame) -> None:
        """
        Creates many-to-many relationships between two entities using data from a DataFrame.
        This function iterates over each row of the provided DataFrame and establishes a relationship between records identified by
        the specified entity column names. For each row, it builds the necessary API endpoint URLs and sends a POST request to connect
        the respective records. The function prints progress messages every 10 processed records and outputs error details when a
        request fails. At the end, it summarizes the number of successful and failed relationship creations.
        Args:
            entity_m (str): Name of the source entity column in the DataFrame, used to construct the primary record reference.
            entity_n (str): Name of the target entity column in the DataFrame, used to construct the related record reference.
            m_to_n_relationship (str): The relationship name that defines how entity_m is related to entity_n in the API.
            df (pd.DataFrame): A DataFrame containing rows with column names matching entity_m and entity_n. Each row represents a pair
                               of records to be linked.
        """
        insert_m_n_headers = dict(self.session.headers)

        successful_updates = 0
        failures = 0
        expected_updates = len(df)

        for idx, row in df.iterrows():
            record_m = row[entity_m]
            record_n = row[entity_n]
            
            requestURI = f'{self.environmentURI}api/data/v9.2/{entity_m}({record_m})/{relationship_name}/$ref'
            odata_id = f'{self.environmentURI}api/data/v9.2/{entity_n}({record_n})'
            payload = { "@odata.id": odata_id }

            r = self.session.post(requestURI, headers=insert_m_n_headers, json=payload)
            
            if r.status_code != 204:
                failures += 1
                logging.error(f'Error linking {record_m} to {record_n}. Error {r.status_code}: \n{r.content.decode('utf-8')}\n')
            
            else:
                successful_updates += 1
                
            if idx % 10 == 0: # type: ignore
                print(f"Processed: {idx + 1}") # type: ignore
                
        print(f'{successful_updates} updates made of {expected_updates} expected updates.\n{failures} failures.') 

    def merge_rows(self, entity: Literal["account", "contact"], df:pd.DataFrame, is_master_col: str, duplicate_family_col: str, perform_parenting_checks:bool = True, primary_key_col = None) -> None:
        """
        Merges duplicate rows into master record in Microsoft Dataverse.
        This function identifies master and subordinate records in the provided DataFrame based on the `is_master_col` and `duplicate_family_col` columns.
        For each master record, it merges all subordinate records that share the same duplicate family ID into the master record using the Dataverse Merge API.
        Args:
            entity (Literal["account", "contact"]): The Dataverse entity type to merge (e.g., "account" or "contact").
            df (pd.DataFrame): The DataFrame containing records to be merged. Must include columns for master/subordinate identification and duplicate family grouping.
            is_master_col (str): The name of the column indicating whether a row is a master record (True) or subordinate (False).
            duplicate_family_col (str): The name of the column that groups records into duplicate families.
            perform_parenting_checks (bool, optional): Whether to perform parenting checks during the merge. Defaults to True.
            primary_key_col (str, optional): The name of the primary key column. If None, defaults to '{entity}id'.
        Note:
            This function sends HTTP POST requests to the Dataverse Merge API for each subordinate to be merged into its master.
            The DataFrame is expected to be pre-processed to identify master and subordinate records.
        """
        merge_headers = dict(self.session.headers)
        merge_headers.update({'Content-Type': 'application/json; charset=utf-8'})
        
        requestURI = f'{self.environmentURI}api/data/v9.2/Merge'
        
        masterDF = df[df[is_master_col] == True]
        subordinateDF = df[df[is_master_col] == False]


        for idx, row in masterDF.iterrows():
            if primary_key_col is None:
                masterID: str = row[f'{entity}id']
            else:
                masterID: str = row[str(primary_key_col)]

            completeRow = row.to_dict()
            completeRow['@odata.type'] = f"Microsoft.Dynamics.CRM.{entity}"
            completeRow.pop(is_master_col, None)
            completeRow.pop(duplicate_family_col, None)
            if primary_key_col is None:
                completeRow.pop(f'{entity}id', None)
            else:
                completeRow.pop(primary_key_col, None)

            duplicateFamilyID = row[duplicate_family_col]
            subordinates = subordinateDF[subordinateDF[duplicate_family_col] == duplicateFamilyID]
            
            if len(subordinates) == 0:
                self.logger.warning(f"No subordinates found for master ID: {masterID} with duplicate family ID: {duplicateFamilyID}. Skipping merge.")
                continue

            self.logger.debug(f"Processing master ID: {masterID} with duplicate family ID: {duplicateFamilyID} found: {len(subordinates)} subordinates.")
            self.logger.debug(completeRow)

            for subordinateIdx, subordinateRow in subordinates.iterrows():
                if primary_key_col is None:
                    subordinateID: str = subordinateRow[f'{entity}id']
                else:
                    subordinateID: str = subordinateRow[primary_key_col]
                
                payload = {
                    "Target": {
                        "@odata.type": f"Microsoft.Dynamics.CRM.{entity}",
                        f"{entity}id": masterID
                    },
                    "Subordinate": {
                        "@odata.type": f"Microsoft.Dynamics.CRM.{entity}",
                        f"{entity}id": subordinateID
                    },
                    "UpdateContent": completeRow,
                    "PerformParentingChecks": perform_parenting_checks
                }

                r = self.session.post(url=requestURI, headers=merge_headers, json=payload)
        
                self.logger.debug(f"requestURI: {r.request.method.upper()} {requestURI}") # type: ignore
                self.logger.debug(f"Headers: {merge_headers}")
                self.logger.debug(f"payload: {json.dumps(payload, indent=4)}")

                if r.status_code != 204:
                    self.logger.error(f"Request failed. Error code: {r.status_code}. Response: {r.content.decode('utf-8')}")
                else:
                    self.logger.debug(f"Request successful")

