courses-pretty.json: courses.json
	jq . courses.json > courses-pretty.json
