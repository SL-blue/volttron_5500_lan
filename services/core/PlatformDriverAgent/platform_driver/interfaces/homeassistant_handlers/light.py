class LightHandler(BaseHandler):
    domain = "light"

    def validate(self, entity_id: str, value: Any, **kwargs) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError(f"Expected numeric value for light brightness, got {type(value)}")

    def set_point(self, entity_id: str, value: Any, **kwargs):
        self.driver.set_light_brightness(entity_id, value)

    def scrape(self, entity_id: str, register, **kwargs):
        brightness = self.driver.get_light_brightness(entity_id)
        register(brightness)