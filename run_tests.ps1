# Set environment variable CLIMODE, so that tests know that they should not plot stuff.
$Env:CLIMODE = "ON"

# Run unittest in discovery mode for the tests folder
& pipenv run python -m unittest discover -v tests -p "*.py"
