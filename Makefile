.PHONY: all
all: plan.out

courses-pretty.json: courses.json
	jq . courses.json > courses-pretty.json

plan.out: hyposchedule.py courses.json blacklisted.in selected.in
	./hyposchedule.py > plan.out
