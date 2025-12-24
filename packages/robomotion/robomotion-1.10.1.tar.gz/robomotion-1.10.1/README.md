# Build and deploy
python setup.py sdist bdist_wheel

pip install twine

twine check dist/*

twine upload dist/*

# Test without uploading
python setup.py sdist bdist_wheel

pip install dist/robomotion-1.8.0-py3-none-any.whl

import robomotion

# Better with venv 
python -m venv testenv
source testenv/bin/activate  # On Windows use `testenv\Scripts\activate`
pip install dist/robomotion-1.8.0-py3-none-any.whl
python -c "import robomotion; print('Library installed and imported successfully')"
deactivate


# Compile
cd robomotion
protoc --proto_path=./protobuf/src/google/protobuf --proto_path=./proto --python_out=. proto/*.proto

# GPT 4.1
python -m grpc_tools.protoc -Irobomotion-python/robomotion/proto -Irobomotion-python/robomotion/protobuf/src --python_out=robomotion-python --grpc_python_out=robomotion-python robomotion-python/robomotion/proto/plugin.proto