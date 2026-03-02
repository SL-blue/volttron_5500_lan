class LockHandler(BaseHandler):
    domain = "lock"

    def validate(self, entity_id: str, value: Any, **kwargs) -> None:
        if not isinstance(value, bool):
            raise ValueError(f"Expected boolean value for lock state, got {type(value)}")

    def set_point(self, entity_id: str, value: Any, **kwargs):
        self.driver.set_lock_state(entity_id, value)

    def scrape(self, entity_id: str, register, **kwargs):
        state = self.driver.get_lock_state(entity_id)
        register(state)