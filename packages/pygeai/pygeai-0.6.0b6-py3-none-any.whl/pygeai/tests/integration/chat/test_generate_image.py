from unittest import TestCase
from pygeai.chat.clients import ChatClient

chat_client: ChatClient

class TestChatGenerateImageIntegration(TestCase):    

    def setUp(self):
        self.chat_client = ChatClient()
        self.new_image = self.__load_image()


    def __load_image(self):
        return {
            "model": "openai/gpt-image-1",
            "prompt": "generate an image of a futuristic city skyline at sunset",
            "n": 1,
            "quality": "high",
            "size": "1024x1536"
        }
    

    def __generate_image(self, image = None):
        image = image if image is not None else self.new_image
        return self.chat_client.generate_image(
            model=image["model"],
            prompt=image["prompt"],
            n=image["n"],
            quality=image["quality"],
            size=image["size"],
            aspect_ratio= image["aspect_ratio"] if "aspect_ratio" in image else None
        )

    
    def test_generate_image(self):
        created_image = self.__generate_image()
        self.assertEqual(len(created_image["data"]), 1, "Expected an image to be generated")


    def test_generate_image_invalid_model(self):
        self.new_image["model"] = "openai/gpt-image-10",
        created_image = self.__generate_image()

        self.assertEqual(
            created_image["error"]["code"], 400,
            "Expected a 400 code for invalid model"
        )
        self.assertEqual(
            created_image["error"]["message"],
            'Provider \'["openai\' does not exists.', 
            "Expected an error message when model does not exists"
        )


    def test_generate_image_no_model(self):
        self.new_image["model"] = ""
        created_image = self.__generate_image()

        self.assertEqual(
            created_image["error"]["message"],
            "LLM Provider NOT provided. Pass in the LLM provider you are trying to call", 
            "Expected an error message when no model is provided"
        )


    def test_generate_image_no_prompt(self):
        self.new_image["prompt"] = ""
        created_image = self.__generate_image()

        self.assertEqual(
            created_image["error"]["type"],
            "invalid_request_error",
            "Expected a 400 code for no model"
        )
        self.assertEqual(
            created_image["error"]["param"], "prompt", 
            "Expected an error message when no model is provided"
        )


    def test_generate_image_specific_n(self):
        self.new_image["n"] = 2

        created_image = self.__generate_image()
        self.assertEqual(len(created_image["data"]), 2, "Expected two images to be generated")


    def test_generate_image_no_n(self):
        self.new_image["n"] = None # default is 1

        created_image = self.__generate_image()
        self.assertEqual(len(created_image["data"]), 1, "Expected an image to be generated")


    def test_generate_image_no_supported_n(self):
        self.new_image["model"] = "openai/dall-e-3"
        self.new_image["n"] = 5

        created_image = self.__generate_image()
        self.assertIn(
            "Invalid 'n': integer above maximum value",
            created_image["error"]["message"],
            "Expected an error message when n is not supported by the model"
        )


    def test_generate_image_no_quality(self):
        self.new_image["quality"] = ""

        created_image = self.__generate_image()
        self.assertIn(
            "Invalid value: ''. Supported values are: 'low', 'medium', 'high', and 'auto'",
            created_image["error"]["message"],
            "Expected an error message when quality is not provided"
        )
    

    def test_generate_image_no_supported_quality(self):
        self.new_image["model"] = "openai/dall-e-3"

        created_image = self.__generate_image()
        self.assertIn(
            "Invalid value: 'high'. Supported values are: 'standard' and 'hd'",
            created_image["error"]["message"],
            "Expected an error message when quality is not supported by the model"
        )


    def test_generate_image_no_size(self):
        self.new_image["size"] = ""

        created_image = self.__generate_image()
        self.assertIn(
            "Invalid value: ''. Supported values are: '1024x1024', '1024x1536', '1536x1024', and 'auto'",
            created_image["error"]["message"],
            "Expected an error message when no size is provided"
        )


    def test_generate_image_no_supported_size(self):
        self.new_image["size"] = 1024
        self.new_image["quality"] = None

        created_image = self.__generate_image()
        self.assertIn(
            "Invalid type for 'size': expected one of '1024x1024', '1024x1536', '1536x1024', or 'auto', but got an integer instead",
            created_image["error"]["message"],
            "Expected an error message when no size is provided"
        )
    

    def test_generate_image_with_aspect_ratio(self):
        self.new_image["model"] = "vertex_ai/imagen-3.0-generate-001"
        self.new_image["aspect_ratio"] = "4:3"
        self.new_image["quality"] = None

        created_image = self.__generate_image()
        self.assertEqual(len(created_image["data"]), 1, "Expected an image to be generated")