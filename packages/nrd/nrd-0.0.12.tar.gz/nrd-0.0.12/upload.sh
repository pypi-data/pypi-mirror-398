exists() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "$1 is installed."
    return 0
  else
    echo "$1 is not installed."
    return 1
  fi
}

project_name=$(awk -F '"' '/^name *=/ {print $2}' pyproject.toml)
echo "building $project_name"
echo "getting PyPI API Token: "
if ( exists op ); then
 api_token=$(op item get "pypi api key" --field "Anmeldedaten" --reveal)
  # shellcheck disable=SC2181
  if [ $? -eq 0 ]; then
  echo "API token retrieved successfully."
  else
    api_token=$(read -s -p "Enter your PyPI API token: ")
  fi
else
  api_token=$(read -s -p "Enter your PyPI API token: ")
fi


uv venv
source .venv/bin/activate
python3 -m ensurepip --upgrade
uv pip install --upgrade pip
uv pip install --upgrade twine
uv pip install --upgrade build

current_version=$(grep "version = " pyproject.toml | sed 's/version = //g' | sed 's/"//g' | sed 's/ //g')
echo "Current version: $current_version"
bumped_version=$(python3 -c "print('$current_version'.split('.')[0] + '.' + '$current_version'.split('.')[1] + '.' + str(int('$current_version'.split('.')[2]) + 1))")
echo "Bumped version: $bumped_version"

read -p "Do you want to upload the new version $bumped_version to PyPI? (y/n) " -n 1 -r confirmation
if [ "$confirmation" == "y" ]; then
  sed -i '' "s/version = \"$current_version\"/version = \"$bumped_version\"/g" pyproject.toml
  rm -rf dist/*
  python3 -m build
  echo "Uploading to PyPI"
  python3 -m twine upload --repository pypi dist/* --user __token__ --password "$api_token"
  pip install --upgrade $project_name
  pip show $project_name
else
  echo "aborting"
fi

