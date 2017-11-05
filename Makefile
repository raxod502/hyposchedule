.PHONY: all
all: plan.out courses-pretty.json

.PHONY: clean
clean:
	@rm -f courses-pretty.json
	@rm -f plan.out

courses.json:
	@echo "Please create courses.json first"
	@false

courses-pretty.json: courses.json
	@command -v jq &>/dev/null && jq . courses.json > courses-pretty.json || true

blacklisted.in:
	@touch blacklisted.in

selected.in:
	@touch selected.in

plan.out: hyposchedule.py courses.json blacklisted.in selected.in
	@./hyposchedule.py
