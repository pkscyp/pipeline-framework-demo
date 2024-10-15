import requests
import json 
from argparse import ArgumentParser
import yaml



def get_functions(base_url,tn_nsp):
     print(f"{base_url}/v3/functions/{tn_nsp}")
     resp = requests.get(f"{base_url}/v3/functions/{tn_nsp}")
     print(resp.status_code)
     if resp.ok:
          funcs = []
          for f in resp.json():
               funcs.append( "/".join([tn_nsp,f]))
          return funcs
     else:
          return []
    
def create_function(base_url,function_def:dict,package_file:str):
    files = { 'functionConfig': ( 'functionConfig', json.dumps(function_def), 'application/json'),
          "data": open(package_file,"rb")
        }
    fqfn = function_def['fqfn']

    resp = requests.post(f"{base_url}/v3/functions/{fqfn}", files=files)
    if resp.ok:
         return {"status":0,'message':'Success'}
    else:
         return {"status":resp.status_code,"message":resp.text}
    
def update_function(base_url,function_def:dict,package_file:str):
    files = { 'functionConfig': ( 'functionConfig', json.dumps(function_def), 'application/json'),
          "data": open(package_file,"rb")
        }
    fqfn = function_def['fqfn']

    resp = requests.put(f"{base_url}/v3/functions/{fqfn}",
                     files=files)
    if resp.ok:
         return {"status":0,'message':'Success'}
    else:
         return {"status":resp.status_code,"message":resp.text}
    

def delete_function(base_url,fn_fqfn):
     resp = requests.delete(f"{base_url}/v3/functions/{fn_fqfn}")
     print(f"{resp.status_code}, {resp.content}")

def get_function_config(base_url,fn_fqfn):
     resp = requests.get(f"{base_url}/v3/functions/{fn_fqfn}")
     if resp.ok:
        print(json.dumps(resp.json(),indent=4))
        return resp.json() 
     else:
          return None

def deploy_action(args):
     print("deploying workflow")
     py_file = args.package
     print(f"Package {py_file}")
     w_file = args.workflow 
     all_configs=[]
     with open(w_file,'r') as input_f:
          fconfigs = yaml.safe_load_all(input_f)
          for fc in fconfigs:
               print(fc)
               if fc:
                    all_configs.append(fc)
     for config in all_configs:
          fn_config = get_function_config(args.adminurl,config['fqfn'])
          if fn_config:
               print("updating function {config['fqfn']}")
               update_function(args.adminurl,config,py_file)
          else:
               print("Creating function {config['fqfn']}")
               create_function(args.adminurl,config,py_file)
               
def create_action(args):
     print("creating function")
     py_file = args.package
     print(f"Package {py_file}")
     fn_file = args.func_config
     with open(fn_file,"r") as fnf:
          fn_cfg = yaml.safe_load(fnf)
          create_function(args.adminurl,fn_cfg,py_file)


def get_action(args):
     print("get all functions")
     funcs = get_functions(args.adminurl,f"{args.tenant}/{args.namespace}")
     print(f"{funcs}")

def update_action(args):
     print("updating function")
     py_file = args.package
     print(f"Package {py_file}")
     fn_file = args.func_config
     with open(fn_file,"r") as fnf:
          fn_cfg = yaml.safe_load(fnf)
          update_function(args.adminurl,fn_cfg,py_file)


def delete_action(args):
     print("deleting function ..")
     delete_function(args.adminurl,args.fqfn)


def main():
    parser = ArgumentParser()
    parser.add_argument("adminurl")
    subparsers = parser.add_subparsers(help='help for subcommand', dest="subcommand")

    parser_deploy = subparsers.add_parser('deploy', help='create workflow')
    parser_deploy.add_argument("-w","--workflow",required=True)
    parser_deploy.add_argument("-p","--package",required=True)
    parser_deploy.set_defaults(func=deploy_action)

    parser_cre = subparsers.add_parser('create', help='create function')
    parser_cre.add_argument("-f","--func_config",required=True)
    parser_cre.add_argument("-p","--package",required=True)
    parser_cre.set_defaults(func=create_action)
    parser_get = subparsers.add_parser('get', help='get help')
    parser_get.add_argument("-t","--tenant",type=str,help="tenant of functions",required=True)
    parser_get.add_argument("-n","--namespace",type=str,help="namespace of function",required=True)
    parser_get.set_defaults(func=get_action)
    parser_upd = subparsers.add_parser('update', help='update workflow')
    parser_upd.add_argument("-f","--func_config")
    parser_upd.add_argument("-p","--package",required=True)
    parser_upd.set_defaults(func=update_action)
    parser_del = subparsers.add_parser('delete', help='delete function')
    parser_del.add_argument("--fqfn",help="fqfn tenant/namespace/functionname")
    parser_del.set_defaults(func=delete_action)


    
    args=parser.parse_args()

    if hasattr(args, "func"):
          args.func(args)
    


if __name__ == "__main__":
     main()