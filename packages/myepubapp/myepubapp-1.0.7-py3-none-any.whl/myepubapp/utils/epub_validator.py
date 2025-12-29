import os
import zipfile
from typing import Dict, Optional

from bs4 import BeautifulSoup

from .logger import setup_logger

logger = setup_logger()


class EPUBValidator:
    """EPUB format validator"""

    def __init__(self) -> None:
        self.namespaces = {
            "opf": "http://www.idpf.org/2007/opf",
            "dc": "http://purl.org/dc/elements/1.1/",
            "xhtml": "http://www.w3.org/1999/xhtml",
        }

    def validate_epub(self, epub_path: str) -> Dict:
        """Validate EPUB file format specifications"""
        results: Dict = {
            "is_valid": True,
            "version": None,
            "errors": [],
            "warnings": [],
            "structure_check": {},
            "metadata_check": {},
            "content_check": {},
        }

        try:
            if not os.path.exists(epub_path):
                results["errors"].append(
                    f"EPUB file does not exist: {epub_path}")
                results["is_valid"] = False
                return results

            with zipfile.ZipFile(epub_path, "r") as zip_ref:
                # Check basic structure
                results["structure_check"] = self._check_structure(zip_ref)

                # Check mimetype
                if "mimetype" not in zip_ref.namelist():
                    results["errors"].append("Missing mimetype file")
                    results["is_valid"] = False
                else:
                    mimetype = zip_ref.read("mimetype").decode("utf-8").strip()
                    if mimetype != "application/epub+zip":
                        results["errors"].append(
                            f"Invalid mimetype: {mimetype}")

                # Check META-INF/container.xml
                container_path = "META-INF/container.xml"
                if container_path not in zip_ref.namelist():
                    results["errors"].append("Missing META-INF/container.xml")
                    results["is_valid"] = False
                else:
                    results["version"] = self._check_container(
                        zip_ref, container_path)

                # Check OPF file
                if results["version"]:
                    opf_path = self._get_opf_path(zip_ref, container_path)
                    if opf_path:
                        results["metadata_check"] = self._check_metadata(
                            zip_ref, opf_path
                        )
                        results["content_check"] = self._check_content(
                            zip_ref, opf_path
                        )
                    else:
                        results["errors"].append("OPF file not found")
                        results["is_valid"] = False

        except Exception as e:
            results["errors"].append(f"Error during validation: {str(e)}")
            results["is_valid"] = False

        return results

    def _check_structure(self, zip_ref: zipfile.ZipFile) -> Dict:
        """Check EPUB basic structure"""
        structure = {
            "has_meta_inf": False,
            "has_epub_folder": False,
            "file_count": len(zip_ref.namelist()),
            "total_size": sum(info.file_size for info in zip_ref.filelist),
        }

        files = zip_ref.namelist()
        structure["has_meta_inf"] = any(
            f.startswith("META-INF/") for f in files)
        structure["has_epub_folder"] = any(
            f.startswith("EPUB/") for f in files)

        return structure

    def _check_container(
        self, zip_ref: zipfile.ZipFile, container_path: str
    ) -> Optional[str]:
        """Check container.xml and return EPUB version"""
        try:
            content = zip_ref.read(container_path).decode("utf-8")
            soup = BeautifulSoup(content, "xml")

            # Find rootfile
            rootfile = soup.find("rootfile")
            if rootfile:
                full_path = rootfile.get("full-path", "")
                # Infer version from OPF file path
                if full_path.startswith("EPUB/"):
                    return "3.0"  # EPUB 3
                else:
                    return "2.0"  # EPUB 2
            else:
                logger.warning("Rootfile element not found")
                return None

        except Exception as e:
            logger.error(f"Error parsing container.xml: {e}")
            return None

    def _get_opf_path(
        self, zip_ref: zipfile.ZipFile, container_path: str
    ) -> Optional[str]:
        """Get OPF file path from container.xml"""
        try:
            content = zip_ref.read(container_path).decode("utf-8")
            soup = BeautifulSoup(content, "xml")

            rootfile = soup.find("rootfile")
            if rootfile:
                full_path = rootfile.get("full-path")
                return full_path if isinstance(full_path, str) else None
        except Exception as e:
            logger.error(f"Error getting OPF path: {e}")
        return None

    def _check_metadata(self, zip_ref: zipfile.ZipFile, opf_path: str) -> Dict:
        """Check metadata in OPF file"""
        metadata = {
            "has_title": False,
            "has_language": False,
            "has_identifier": False,
            "has_creator": False,
            "title": None,
            "language": None,
            "identifier": None,
        }

        try:
            content = zip_ref.read(opf_path).decode("utf-8")
            soup = BeautifulSoup(content, "xml")

            # Check metadata element
            metadata_elem = soup.find("metadata")
            if metadata_elem:
                # Check required metadata
                title = metadata_elem.find("dc:title")
                if title:
                    metadata["has_title"] = True
                    metadata["title"] = title.get_text()

                language = metadata_elem.find("dc:language")
                if language:
                    metadata["has_language"] = True
                    metadata["language"] = language.get_text()

                identifier = metadata_elem.find("dc:identifier")
                if identifier:
                    metadata["has_identifier"] = True
                    metadata["identifier"] = identifier.get_text()

                creator = metadata_elem.find("dc:creator")
                if creator:
                    metadata["has_creator"] = True

        except Exception as e:
            logger.error(f"Error checking metadata: {e}")

        return metadata

    def _check_content(self, zip_ref: zipfile.ZipFile, opf_path: str) -> Dict:
        """Check content files"""
        content = {
            "has_spine": False,
            "has_toc": False,
            "spine_items": 0,
            "manifest_items": 0,
            "xhtml_files": 0,
            "css_files": 0,
            "image_files": 0,
        }

        try:
            content_data = zip_ref.read(opf_path).decode("utf-8")
            soup = BeautifulSoup(content_data, "xml")

            # Check spine
            spine = soup.find("spine")
            if spine:
                content["has_spine"] = True
                content["spine_items"] = len(spine.find_all("itemref"))

            # Check manifest
            manifest = soup.find("manifest")
            if manifest:
                items = manifest.find_all("item")
                content["manifest_items"] = len(items)

                for item in items:
                    media_type = item.get("media-type", "")
                    if media_type == "application/xhtml+xml":
                        content["xhtml_files"] += 1
                    elif media_type == "text/css":
                        content["css_files"] += 1
                    elif media_type.startswith("image/"):
                        content["image_files"] += 1

            # Check TOC
            guide = soup.find("guide")
            if guide:
                content["has_toc"] = True

        except Exception as e:
            logger.error(f"Error checking content: {e}")

        return content

    def print_validation_report(self, results: Dict) -> None:
        """Print validation report"""
        print("=== EPUB Validation Report ===")
        print(f"File Validity: {'✓' if results['is_valid'] else '✗'}")
        print(f"EPUB Version: {results.get('version', 'Unknown')}")

        if results["errors"]:
            print("\n❌ Errors:")
            for error in results["errors"]:
                print(f"  - {error}")

        if results["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in results["warnings"]:
                print(f"  - {warning}")

        print("\n📊 Structure Check:")
        structure = results.get("structure_check", {})
        print(f"  - Total Files: {structure.get('file_count', 0)}")
        print(f"  - Total Size: {structure.get('total_size', 0)} bytes")
        print(
            f"  - Has META-INF: {'✓' if structure.get('has_meta_inf') else '✗'}")
        print(
            f"  - Has EPUB Folder: {'✓' if structure.get('has_epub_folder') else '✗'}"
        )

        print("\n📋 Metadata Check:")
        metadata = results.get("metadata_check", {})
        print(f"  - Has Title: {'✓' if metadata.get('has_title') else '✗'}")
        print(
            f"  - Has Language: {'✓' if metadata.get('has_language') else '✗'}")
        print(
            f"  - Has Identifier: {'✓' if metadata.get('has_identifier') else '✗'}")
        print(
            f"  - Has Creator: {'✓' if metadata.get('has_creator') else '✗'}")

        print("\n📖 Content Check:")
        content_check = results.get("content_check", {})
        print(
            f"  - Has Spine: {'✓' if content_check.get('has_spine') else '✗'}")
        print(f"  - Has TOC: {'✓' if content_check.get('has_toc') else '✗'}")
        print(f"  - Spine Items: {content_check.get('spine_items', 0)}")
        print(f"  - XHTML Files: {content_check.get('xhtml_files', 0)}")
        print(f"  - CSS Files: {content_check.get('css_files', 0)}")
        print(f"  - Image Files: {content_check.get('image_files', 0)}")
