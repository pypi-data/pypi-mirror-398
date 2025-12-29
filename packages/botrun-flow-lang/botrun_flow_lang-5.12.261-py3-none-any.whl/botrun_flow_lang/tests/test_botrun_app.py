import unittest
from botrun_flow_lang.models.botrun_app import BotrunApp, BotrunAppMode


class TestBotrunApp(unittest.TestCase):
    def test_to_yaml(self):
        app = BotrunApp(
            name="Test App",
            description="A test application",
            mode=BotrunAppMode.CHATBOT,
        )
        yaml_str = app.to_yaml()
        self.assertIn("name: Test App", yaml_str)
        self.assertIn("description: A test application", yaml_str)
        self.assertIn("mode: chatbot", yaml_str)

    def test_from_yaml(self):
        yaml_str = """
        name: Test App
        description: A test application
        mode: workflow
        """
        app = BotrunApp.from_yaml(yaml_str)
        self.assertEqual(app.name, "Test App")
        self.assertEqual(app.description, "A test application")
        self.assertEqual(app.mode, BotrunAppMode.WORKFLOW)

    def test_roundtrip(self):
        original_app = BotrunApp(
            name="Test App",
            description="A test application",
            mode=BotrunAppMode.CHATBOT,
        )
        yaml_str = original_app.to_yaml()
        reconstructed_app = BotrunApp.from_yaml(yaml_str)
        self.assertEqual(original_app, reconstructed_app)

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            BotrunApp(
                name="Test App", description="A test application", mode="invalid_mode"
            )


if __name__ == "__main__":
    unittest.main()
