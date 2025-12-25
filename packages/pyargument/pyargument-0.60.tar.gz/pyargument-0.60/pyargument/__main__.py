from . import PyArgument
import json
import os

def main():
    pwd = os.getcwd()
    parser = PyArgument()
    parser.add_arg("--online")
    parser.add_arg("--input", "-in", optarg=True, required=True)
    parser.add_arg("--dir", "--folder", optarg=True, default=pwd)
    parser.add_arg("--file", optarg=True)
    parser.add_arg("--pwd", "-p", "--cwd", required=True)

    parser.parse_args()
    
    print("Collected args:", parser.pyargs)
    print("Arguments metadata:", json.dumps(parser.list_meta(), indent=4))
    print("Arguments provided:", parser.list_args())
    print("Arguments alias:", json.dumps(parser.list_alias(), indent=4))
    print("online:", parser.online)
    print("input:", parser.input)
    print("dir:", parser.dir, "is exists:", parser.dir.exists, "metadata:", parser.dir.meta)
    print("file:", parser.file)
    parser.file.value = "new_value.txt"
    print("file:", parser.file.value) # argument value changed!
    print("pwd:", parser.pwd)

if __name__ == "__main__":
    main()