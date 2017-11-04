.PHONY: all
all: plan.out

courses.json:
	@echo "Please create courses.json first"
	@false

courses-pretty.json: courses.json
	jq . courses.json > courses-pretty.json

blacklisted.in:
	touch blacklisted.in

selected.in:
	touch selected.in

plan.out: hyposchedule.py courses.json blacklisted.in selected.in
	./hyposchedule.py > plan.out
