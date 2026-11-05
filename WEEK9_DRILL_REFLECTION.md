# Setup


# Part A
A2.  app/services/tasks.py
Before prompt: Coverage: 45%, Missing: 18, 24, 29-31, 37-42, 60-63, 70, 72, 78-94, 99-102, 107-109
After prompt: Coverage: 100%, Missing: N/A

A4. 
    @pytest.mark.parametrize("priority", PRIORITIES)
    def test_each_allowed_priority_is_accepted(self, priority):
        assert create_task("t", priority=priority).priority == priority

    @pytest.mark.parametrize("priority", BAD_PRIORITIES)
    def test_invalid_priority_is_rejected(self, priority):
        with pytest.raises(ValidationError) as exc:
            create_task("t", priority=priority)
        assert exc.value.message == PRIORITY_INVALID

    def test_due_date_accepts_date_object(self):
        assert create_task("t", due_date=date(2026, 12, 31)).due_date == date(2026, 12, 31)

# Part B


# Reflection