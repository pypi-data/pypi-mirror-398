"""
Docker 構成検出器
"""

from pathlib import Path
import re

from ..models import Service


class DockerDetector:
    """Docker 構成を検出"""

    def detect(self, project_root: Path) -> list[Service]:
        services = []

        # Dockerfile の検出
        dockerfile = project_root / "Dockerfile"
        if dockerfile.exists():
            service = self._parse_dockerfile(dockerfile)
            if service:
                services.append(service)

        return services

    def _parse_dockerfile(self, path: Path) -> Service | None:
        """Dockerfile をパース"""
        ports = []
        with open(path) as f:
            for line in f:
                # EXPOSE 行を探す
                if line.strip().startswith("EXPOSE"):
                    port_match = re.search(r"EXPOSE\s+(\d+)", line)
                    if port_match:
                        ports.append(int(port_match.group(1)))

        if ports:
            return Service(
                name="docker-service",
                type="docker",
                ports=ports,
                description="Dockerized service",
            )
        return None
