"""
ベンチマーク機能の統合テスト
"""

from docgen.benchmark import BenchmarkRecorder, BenchmarkReporter
from docgen.docgen import DocGen


class TestBenchmarkIntegration:
    """ベンチマーク機能の統合テスト"""

    def test_benchmark_with_document_generation(self, temp_project):
        """ドキュメント生成時のベンチマーク測定の統合テスト"""
        # プロジェクトファイルを作成
        (temp_project / "src").mkdir()
        (temp_project / "src" / "__init__.py").write_text("")
        (temp_project / "src" / "main.py").write_text(
            '''
def hello(name: str) -> str:
    """Say hello.

    Args:
        name: Name to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"
'''
        )

        # 設定ファイルを作成（ベンチマークを有効化）
        (temp_project / "docgen").mkdir(exist_ok=True)
        (temp_project / "docgen" / "config.toml").write_text(
            """
[generation]
generate_api_doc = true
update_readme = true
generate_agents_doc = false

[benchmark]
enabled = true
"""
        )

        # レコーダーをリセット
        BenchmarkRecorder.reset_global()
        recorder = BenchmarkRecorder.get_global()

        # DocGenを実行
        docgen = DocGen(project_root=temp_project)
        docgen.update_config({"benchmark.enabled": True})
        result = docgen.generate_documents()

        assert result is True

        # ベンチマーク結果が記録されていることを確認
        results = recorder.get_results()
        assert len(results) > 0

        # レポート生成が動作することを確認
        reporter = BenchmarkReporter(recorder)
        markdown = reporter.generate_markdown()
        assert "ベンチマーク結果" in markdown
        assert len(results) > 0

        # JSONエクスポートが動作することを確認
        json_data = reporter.generate_json()
        assert "total_duration" in json_data
        assert "results" in json_data

    def test_benchmark_csv_export(self, temp_project):
        """CSVエクスポート機能の統合テスト"""
        # プロジェクトファイルを作成
        (temp_project / "src").mkdir()
        (temp_project / "src" / "__init__.py").write_text("")

        # 設定ファイルを作成
        (temp_project / "docgen").mkdir(exist_ok=True)
        (temp_project / "docgen" / "config.toml").write_text(
            """
[generation]
generate_api_doc = true
update_readme = false
generate_agents_doc = false

[benchmark]
enabled = true
"""
        )

        # レコーダーをリセット
        BenchmarkRecorder.reset_global()
        recorder = BenchmarkRecorder.get_global()

        # DocGenを実行
        docgen = DocGen(project_root=temp_project)
        docgen.update_config({"benchmark.enabled": True})
        docgen.generate_documents()

        # CSVエクスポート
        reporter = BenchmarkReporter(recorder)
        csv_output = temp_project / "benchmark.csv"
        reporter.save_csv(csv_output)

        # CSVファイルが生成されていることを確認
        assert csv_output.exists()
        content = csv_output.read_text(encoding="utf-8")
        assert "処理名" in content
        assert "実行時間(秒)" in content

    def test_benchmark_comparison(self, temp_project):
        """ベンチマーク比較機能の統合テスト"""
        from docgen.benchmark import BenchmarkComparator

        # プロジェクトファイルを作成
        (temp_project / "src").mkdir()
        (temp_project / "src" / "__init__.py").write_text("")

        # 設定ファイルを作成
        (temp_project / "docgen").mkdir(exist_ok=True)
        (temp_project / "docgen" / "config.toml").write_text(
            """
[generation]
generate_api_doc = true
update_readme = false
generate_agents_doc = false

[benchmark]
enabled = true
"""
        )

        # 1回目のベンチマーク実行
        BenchmarkRecorder.reset_global()
        docgen1 = DocGen(project_root=temp_project)
        docgen1.update_config({"benchmark.enabled": True})
        docgen1.generate_documents()

        baseline_path = temp_project / "baseline.json"
        reporter1 = BenchmarkReporter(BenchmarkRecorder.get_global())
        reporter1.save_json(baseline_path)

        # 2回目のベンチマーク実行
        BenchmarkRecorder.reset_global()
        docgen2 = DocGen(project_root=temp_project)
        docgen2.update_config({"benchmark.enabled": True})
        docgen2.generate_documents()

        current_path = temp_project / "current.json"
        reporter2 = BenchmarkReporter(BenchmarkRecorder.get_global())
        reporter2.save_json(current_path)

        # 比較実行
        comparator = BenchmarkComparator(baseline_path, current_path)
        comparison = comparator.compare()

        assert "baseline" in comparison
        assert "current" in comparison
        assert "comparisons" in comparison
        assert len(comparison["comparisons"]) > 0

        # 比較レポート生成
        report = comparator.generate_comparison_report()
        assert "ベンチマーク比較レポート" in report

    def test_benchmark_disabled(self, temp_project):
        """ベンチマークが無効な場合のテスト"""
        # プロジェクトファイルを作成
        (temp_project / "src").mkdir()
        (temp_project / "src" / "__init__.py").write_text("")

        # 設定ファイルを作成（ベンチマーク無効）
        (temp_project / "docgen").mkdir(exist_ok=True)
        (temp_project / "docgen" / "config.toml").write_text(
            """
[generation]
generate_api_doc = true
update_readme = false
generate_agents_doc = false

[benchmark]
enabled = false
"""
        )

        # レコーダーをリセット
        BenchmarkRecorder.reset_global()
        recorder = BenchmarkRecorder.get_global()

        # DocGenを実行
        docgen = DocGen(project_root=temp_project)
        result = docgen.generate_documents()

        assert result is True

        # ベンチマーク結果が記録されていないことを確認
        results = recorder.get_results()
        assert len(results) == 0
