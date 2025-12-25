from typing import List

from sayou.core.registry import register_component

from ..core.exceptions import WriterError
from ..interfaces.base_writer import BaseWriter

try:
    from neo4j import GraphDatabase
except ImportError:
    raise ImportError(
        "Neo4jWriter requires 'neo4j'. Install with 'pip install sayou-loader[neo4j]'"
    )


@register_component("writer")
class Neo4jWriter(BaseWriter):
    """
    Executes Cypher queries against a Neo4j database.
    """

    component_name = "Neo4jWriter"
    SUPPORTED_TYPES = ["neo4j", "graphdb", "cypher"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        """
        Determines eligibility based on destination format (ext) or connection string.
        """
        if GraphDatabase is None:
            return 0.0

        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if strategy == "auto" and destination:
            if destination.startswith("bolt://") or destination.startswith("neo4j://"):
                return 1.0

        return 0.0

    def initialize(self, **kwargs):
        """
        Initialize Neo4j Driver.
        Expects: neo4j_uri (or uses destination from run), neo4j_user, neo4j_password
        """
        if GraphDatabase is None:
            raise ImportError(
                "Neo4jWriter requires 'neo4j'. Install with 'pip install sayou-loader[neo4j]'"
            )

        self.auth_config = kwargs
        self.driver = None

    def _ensure_connection(self, uri: str):
        """Lazy connection helper"""
        if self.driver:
            return

        user = self.auth_config.get("neo4j_user", "neo4j")
        password = self.auth_config.get("neo4j_password", "password")

        if not (uri.startswith("bolt://") or uri.startswith("neo4j://")):
            uri = self.auth_config.get("neo4j_uri", uri)

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self._log(f"Neo4j driver connected to {uri}.")
        except Exception as e:
            raise WriterError(f"Failed to connect to Neo4j at {uri}: {e}")

    def __del__(self):
        if hasattr(self, "driver") and self.driver:
            self.driver.close()

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        """
        Execute Cypher queries.
        Args:
            input_data: List of Cypher query strings.
            destination: Neo4j URI (e.g., bolt://localhost:7687).
        """
        self._ensure_connection(destination)

        if not isinstance(input_data, list):
            self._log("Neo4jWriter expects a list of Cypher strings.", level="error")
            return False

        # Transaction execution
        success_count = 0
        with self.driver.session() as session:
            for query in input_data:
                try:
                    # 간단한 실행 (실제로는 배치 처리나 파라미터 바인딩 권장)
                    session.run(query)
                    success_count += 1
                except Exception as e:
                    self._log(f"Cypher query failed: {e}", level="warning")
                    # 실패해도 계속 진행할지 여부는 정책에 따름 (여기선 진행)

        self._log(f"Executed {success_count}/{len(input_data)} queries successfully.")
        return True
