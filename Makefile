out_files := plan.out inverse-plan.out sections.out inverse-sections.out

.PHONY: all
all: $(out_files) courses-pretty.json

.PHONY: clean
clean:
	@rm -f courses-pretty.json
	@rm -f $(out_files)

courses.json:
	@echo "Please create courses.json first"
	@false

courses-pretty.json: courses.json
	@command -v jq &>/dev/null && jq . courses.json > courses-pretty.json || true

blacklisted.in:
	@touch blacklisted.in

selected.in:
	@touch selected.in

$(out_files): hyposchedule.py courses.json blacklisted.in selected.in
	@./hyposchedule.py
