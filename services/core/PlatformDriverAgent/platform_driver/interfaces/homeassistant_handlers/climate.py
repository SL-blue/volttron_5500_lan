class ClimateHandler(BaseHandler):
    domain = "climate"

    def validate(self, entity_id: str, value: Any, **kwargs) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError(f"Expected numeric value for climate temperature set point, got {type(value)}")

    def set_point(self, entity_id: str, value: Any, **kwargs):
        self.driver.set_climate_temperature(entity_id, value)

    def scrape(self, entity_id: str, register, **kwargs):
        temperature = self.driver.get_climate_temperature(entity_id)
        register(temperature)