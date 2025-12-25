"""Unit tests for CSV to YAML converter using fixture files."""

from pathlib import Path

import pytest

from main import csv_to_yaml, yaml_to_csv, csv_file_to_yaml_file, yaml_file_to_csv_file


class TestCsvToYaml:
    """Tests for CSV to YAML conversion."""

    def test_english_csv_to_dict(self, english_csv):
        result = csv_to_yaml(english_csv)
        assert len(result) == 3
        assert result[1] == {"name": "Alice", "age": "30", "city": "New York"}
        assert result[2] == {"name": "Bob", "age": "25", "city": "Los Angeles"}
        assert result[3] == {"name": "Charlie", "age": "35", "city": "Chicago"}

    def test_english_csv_to_yaml_string(self, english_csv):
        result = csv_to_yaml(english_csv, as_string=True)
        assert "name: Alice" in result
        assert "city: New York" in result

    def test_korean_csv_to_dict(self, korean_csv):
        result = csv_to_yaml(korean_csv)
        assert len(result) == 3
        assert result[1]["이름"] == "김철수"
        assert result[1]["도시"] == "서울"
        assert result[2]["이름"] == "박영희"
        assert result[3]["이름"] == "이민수"

    def test_korean_csv_to_yaml_string(self, korean_csv):
        result = csv_to_yaml(korean_csv, as_string=True)
        assert "이름: 김철수" in result
        assert "도시: 서울" in result

    def test_mixed_csv_to_dict(self, mixed_csv):
        result = csv_to_yaml(mixed_csv)
        assert len(result) == 3
        assert result[1]["ID"] == "1"
        assert result[1]["이름"] == "홍길동"
        assert result[1]["name"] == "Hong Gildong"
        assert result[1]["Email"] == "hong@test.com"
        assert result[1]["전화번호"] == "010-1234-5678"

    def test_special_chars_csv_to_dict(self, special_chars_csv):
        result = csv_to_yaml(special_chars_csv)
        assert result[1]["address"] == "123 Main St, Apt 4"
        assert result[1]["quote"] == 'She said "hello"'
        assert result[2]["address"] == "456 Oak Ave, Suite 100"

    def test_empty_csv_to_dict(self, empty_csv):
        result = csv_to_yaml(empty_csv)
        assert result == {}

    def test_csv_path_as_string(self, english_csv):
        result = csv_to_yaml(str(english_csv))
        assert len(result) == 3
        assert result[1]["name"] == "Alice"


class TestYamlToCsv:
    """Tests for YAML to CSV conversion."""

    def test_english_yaml_to_dict(self, english_yaml):
        result = yaml_to_csv(english_yaml)
        assert len(result) == 3
        assert result[0] == {"name": "Alice", "age": 30, "city": "New York"}
        assert result[1] == {"name": "Bob", "age": 25, "city": "Los Angeles"}

    def test_english_yaml_to_csv_string(self, english_yaml):
        result = yaml_to_csv(english_yaml, as_string=True)
        assert "name,age,city" in result
        assert "Alice,30,New York" in result

    def test_korean_yaml_to_dict(self, korean_yaml):
        result = yaml_to_csv(korean_yaml)
        assert len(result) == 3
        assert result[0]["이름"] == "김철수"
        assert result[0]["나이"] == 30
        assert result[0]["도시"] == "서울"

    def test_korean_yaml_to_csv_string(self, korean_yaml):
        result = yaml_to_csv(korean_yaml, as_string=True)
        assert "이름,나이,도시" in result
        assert "김철수,30,서울" in result

    def test_mixed_yaml_to_dict(self, mixed_yaml):
        result = yaml_to_csv(mixed_yaml)
        assert len(result) == 3
        assert result[0]["ID"] == 1
        assert result[0]["이름"] == "홍길동"
        assert result[0]["name"] == "Hong Gildong"

    def test_single_object_yaml_to_dict(self, single_object_yaml):
        result = yaml_to_csv(single_object_yaml)
        assert result == [{"name": "Alice", "age": 30, "city": "New York"}]

    def test_multiline_yaml_to_dict(self, multiline_yaml):
        result = yaml_to_csv(multiline_yaml)
        assert len(result) == 2
        assert "Line 1" in result[0]["bio"]
        assert "Line 2" in result[0]["bio"]


class TestFileToFile:
    """Tests for file-to-file conversion functions."""

    def test_csv_file_to_yaml_file(self, english_csv, tmp_path):
        output_yaml = tmp_path / "output.yaml"
        csv_file_to_yaml_file(english_csv, output_yaml)

        assert output_yaml.exists()
        content = output_yaml.read_text(encoding="utf-8")
        assert "name: Alice" in content
        assert "city: New York" in content

    def test_yaml_file_to_csv_file(self, english_yaml, tmp_path):
        output_csv = tmp_path / "output.csv"
        yaml_file_to_csv_file(english_yaml, output_csv)

        assert output_csv.exists()
        content = output_csv.read_text(encoding="utf-8")
        assert "name,age,city" in content
        assert "Alice,30,New York" in content

    def test_korean_csv_to_yaml_file(self, korean_csv, tmp_path):
        output_yaml = tmp_path / "korean_output.yaml"
        csv_file_to_yaml_file(korean_csv, output_yaml)

        assert output_yaml.exists()
        content = output_yaml.read_text(encoding="utf-8")
        assert "이름: 김철수" in content
        assert "도시: 서울" in content

    def test_korean_yaml_to_csv_file(self, korean_yaml, tmp_path):
        output_csv = tmp_path / "korean_output.csv"
        yaml_file_to_csv_file(korean_yaml, output_csv)

        assert output_csv.exists()
        content = output_csv.read_text(encoding="utf-8")
        assert "이름,나이,도시" in content
        assert "김철수,30,서울" in content


class TestRoundTrip:
    """Tests for roundtrip conversion (CSV -> YAML -> CSV and YAML -> CSV -> YAML)."""

    def test_english_csv_roundtrip(self, english_csv, tmp_path):
        yaml_file = tmp_path / "intermediate.yaml"
        csv_output = tmp_path / "output.csv"

        csv_file_to_yaml_file(english_csv, yaml_file)
        yaml_file_to_csv_file(yaml_file, csv_output)

        original = english_csv.read_text(encoding="utf-8").strip()
        result = csv_output.read_text(encoding="utf-8").strip()

        original_lines = set(original.split("\n"))
        result_lines = set(result.split("\n"))
        assert original_lines == result_lines

    def test_korean_csv_roundtrip(self, korean_csv, tmp_path):
        yaml_file = tmp_path / "intermediate.yaml"
        csv_output = tmp_path / "output.csv"

        csv_file_to_yaml_file(korean_csv, yaml_file)
        yaml_file_to_csv_file(yaml_file, csv_output)

        original = korean_csv.read_text(encoding="utf-8").strip()
        result = csv_output.read_text(encoding="utf-8").strip()

        original_lines = set(original.split("\n"))
        result_lines = set(result.split("\n"))
        assert original_lines == result_lines

    def test_mixed_csv_roundtrip(self, mixed_csv, tmp_path):
        yaml_file = tmp_path / "intermediate.yaml"
        csv_output = tmp_path / "output.csv"

        csv_file_to_yaml_file(mixed_csv, yaml_file)
        yaml_file_to_csv_file(yaml_file, csv_output)

        original = mixed_csv.read_text(encoding="utf-8").strip()
        result = csv_output.read_text(encoding="utf-8").strip()

        original_lines = set(original.split("\n"))
        result_lines = set(result.split("\n"))
        assert original_lines == result_lines

    def test_english_yaml_roundtrip(self, english_yaml, tmp_path):
        csv_file = tmp_path / "intermediate.csv"
        yaml_output = tmp_path / "output.yaml"

        yaml_file_to_csv_file(english_yaml, csv_file)
        csv_file_to_yaml_file(csv_file, yaml_output)

        original_data = yaml_to_csv(english_yaml)
        result_data = yaml_to_csv(yaml_output)

        assert len(original_data) == len(result_data)
        for orig, res in zip(original_data, result_data):
            assert orig["name"] == res["name"]
            assert str(orig["age"]) == str(res["age"])
            assert orig["city"] == res["city"]


class TestStringInput:
    """Tests for string input (not file paths)."""

    def test_csv_string_input(self):
        csv_data = "name,age\nAlice,30\nBob,25"
        result = csv_to_yaml(csv_data)
        assert len(result) == 2
        assert result[1]["name"] == "Alice"

    def test_yaml_string_input(self):
        yaml_data = "- name: Alice\n  age: 30"
        result = yaml_to_csv(yaml_data)
        assert result == [{"name": "Alice", "age": 30}]

    def test_korean_csv_string_input(self):
        csv_data = "이름,나이\n홍길동,30"
        result = csv_to_yaml(csv_data)
        assert result[1]["이름"] == "홍길동"

    def test_korean_yaml_string_input(self):
        yaml_data = "- 이름: 홍길동\n  나이: 30"
        result = yaml_to_csv(yaml_data)
        assert result[0]["이름"] == "홍길동"
        assert result[0]["나이"] == 30
