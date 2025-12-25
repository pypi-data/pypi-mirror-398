class Provider:
    def __init__(self, attr):
        self.meta = attr
        
        for key, value in attr.items():
            setattr(self, key, value)

    # Make the object behave like the self.value
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __bool__(self):
        return bool(self.value)
        
    # allow operations by returning the original value
    def __add__(self, next):
        return self.value + next
        #return self.value.__add__(next)
        
    def __radd__(self, prev):
        return prev + self.value
        #return prev.__add__(self.value)
        
    def __fspath__(self):
        return str(self.value)
    
    def __getattr__(self, name):
        return getattr(self.value, name) # let object works with another method that are not belongs to this object by using getattr
        # self.value -> Object value type (str, int, float, etc.)
        # name -> missing method name (upper, split, etc.)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name != "meta":
            self.meta[name] = value

class PyArgument:
    def __init__(self):
        self.pyargs = []
        self.attrs = {}
        self.arg_map = {}
        
    def list_meta(self):
        return {
            key: obj.meta
            for key, obj in self.attrs.items()
                }
        
    def list_alias(self):
        alias = {}
        for key, value in self.arg_map.items():
            if value not in alias:
                alias[value] = []
            alias[value].append(key)
        return alias
        
    def list_args(self):
        # returning list of existed args.
        return [arg for arg in self.attrs if self.attrs[arg].exists]
    
    def add_arg(self, *names, optarg=False, default=None, required=False):
        if not names:
            raise ValueError("At least one argument name must be provided.")
            
        # Pick the first long name, else first name
        argname = ""
        for arg in names:
            if arg.startswith("--"):
                argname = arg[2::]
                break
                
        if not argname: names[0].lstrip("-")
        argvalue = default # if optarg else False
        
        
        attr = {
            "value": argvalue,
            "optarg": optarg,
            "required": required,
            "names": names,
            "exists": False
        }
        
        # Setting all attrs to the provider Object.
        providerObj = Provider(attr)
        
        # Setting argument dict.
        self.attrs[argname] = providerObj
        
        # Map all names to argname.
        for arg in names:
            self.arg_map[arg] = argname
        
        # Setting argument attribute for instenses (object)
        setattr(self, argname, providerObj)
    
    # Parse command line arguments
    def parse_args(self, *args):
        import sys
        # Capture all arguments expect script name.
        nargs = sys.argv[1::]
        
        # Loop throught all command line arguments
        for i, arg in enumerate(nargs):
            
            # Only handle arguments that exists in arg_map.
            if any(name for name in self.arg_map if name in arg):
                internal_name = [name for name in self.arg_map if name in arg][0]
                argstart = arg.lstrip("-")
                
                argtype = 0
                argname = ""
                argvalue = ""
                
                # Extract argument name until the "=" comes.
                for j in range(len(argstart)):
                    if argstart[j] != "=":
                        argname += argstart[j]
                    else:
                        # Break the loop if "=" comes.
                        argtype = 1
                        break
                
                # Extract the value after "=" and start where index of "=".
                for k in range(1, j+len(argstart)):
                    if j+k < len(argstart): # Make sure loop did not go out of index.
                        argvalue += argstart[j+k]
                        
                argname = self.arg_map[internal_name]
                    
                try:
                    providerObj = self.attrs[argname] # Gets aegument metadata from dict.
                except:
                    continue
                
                # Check if argument accept value.
                if providerObj.optarg:
                    # Checks if next value is NOT greater than i+1 index either another flag.
                    if i+1 < len(nargs) and not nargs[i+1].startswith("-"):
                        argvalue = nargs[i+1] # Store next argument.
                else:
                    argvalue = True
                    
                if (
                    (providerObj.value and not argvalue) or
                    (not providerObj.value and not argvalue)
                ):
                    argvalue = providerObj.value
                
                # Updates the providerObj.value.
                providerObj.value = argvalue
                
                if argvalue and argname: # Updates the argument attribute on argvalue condition.
                    providerObj.exists = True
                else:
                    providerObj.exists = False
                
                # Push collected internal args to pyargs.
                if argtype == 0:
                    self.pyargs.append(internal_name)
                    if argvalue is not True:
                        self.pyargs.append(argvalue)
                elif argvalue is not True:
                    self.pyargs.append(arg)
                
        # Check required arguments
        unavailable_args = []
        for k, obj in self.attrs.items():
            if obj.required and not obj.value:
                unavailable_args.append(f"Required argument {v['names']} not provided.")
        if len(unavailable_args) > 0:
            for args in unavailable_args:
                print(args)
            sys.exit(1)
