from pygeai.lab.managers import AILabManager

import uuid

from pygeai.lab.models import Tool

# Define the tool
tool_id = str(uuid.uuid4())

open_api_json = {
    "openapi": "3.0.1",
    "info": {
        "title": "Headless Browser Web Scraper",
        "description": "A tool for scraping web pages with JavaScript execution and headless browser emulation.",
        "version": "1.0.0"
    },
    "paths": {
        "/web_scraper/headless_browser": {
            "post": {
                "summary": "Scrape a web page with JavaScript execution",
                "description": "This endpoint allows you to scrape web pages, including dynamically loaded content, using a headless browser.",
                "operationId": "scrapeWebPage",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string",
                                        "description": "The URL of the web page to scrape.",
                                        "example": "https://example.com"
                                    },
                                    "waitForSelector": {
                                        "type": "string",
                                        "description": "A CSS selector to wait for before scraping the page.",
                                        "example": "#content"
                                    },
                                    "timeout": {
                                        "type": "integer",
                                        "description": "Maximum time to wait for the page to load (in milliseconds).",
                                        "example": 10000
                                    },
                                    "actions": {
                                        "type": "array",
                                        "description": "A list of actions to perform on the page.",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "actionType": {
                                                    "type": "string",
                                                    "description": "The type of action to perform (e.g., click, type).",
                                                    "example": "click"
                                                },
                                                "selector": {
                                                    "type": "string",
                                                    "description": "The CSS selector for the element to interact with.",
                                                    "example": "#submit-button"
                                                },
                                                "value": {
                                                    "type": "string",
                                                    "description": "The value to use for the action (e.g., text to type).",
                                                    "example": "Hello World"
                                                }
                                            }
                                        }
                                    }
                                },
                                "required": ["url"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successfully scraped the web page.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "html": {
                                            "type": "string",
                                            "description": "The HTML content of the scraped page."
                                        },
                                        "screenshot": {
                                            "type": "string",
                                            "description": "A base64-encoded screenshot of the page."
                                        },
                                        "data": {
                                            "type": "object",
                                            "description": "Extracted data from the page."
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request parameters."
                    },
                    "500": {
                        "description": "Internal server error."
                    }
                }
            }
        }
    }
}

tool = Tool(
    id=tool_id,
    status="active",
    name="HeadlessBrowserWebScrapper",
    access_scope="private",
    public_name="com.globant.web.scraper.headless",
    description="Scrapes web pages, including dynamically loaded content, using headless browser emulation.",
    scope="api",
    open_api_json=open_api_json
)

# Create the tool
manager = AILabManager()
result = manager.create_tool(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    tool=tool
)

if isinstance(result, Tool):
    print(f"Tool created successfully: {tool.to_dict()}")
else:
    print("Errors:", result.errors if hasattr(result, 'errors') else "Unknown error occurred")