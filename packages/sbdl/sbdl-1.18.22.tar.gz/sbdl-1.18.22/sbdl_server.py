#!/usr/bin/python3
_G='SBDL_COMMAND'
_F='HANDLE_DELAY'
_E='utf-8'
_D=False
_C='API_KEY'
_B=True
_A=None
import base64,datetime
from http.server import BaseHTTPRequestHandler,HTTPServer
import io,json,os,subprocess,sys,tarfile,tempfile,time
API_VERSION='1.1.0'
API_NAME='sbdl'
API_FUNCTIONS={}
def get_config_value(key):
	C={_F:2,_G:'sbdl',_C:''};A=C[key];D=f"sbdl_{key}".upper();B=os.getenv(D)
	if B is not _A:A=B
	return A
def get_date_string():return datetime.datetime.now().isoformat()
def send_data(content):print(content)
def response_message(message,is_success=_B):
	A='Status:'
	if is_success:A+=' 200 OK'
	else:A+=' 400 Bad Request'
	A+='\r\n';send_data(A+'Content-Type: application/json\r\n\r\n');send_data(message)
def exec_external(command_list,working_dir=_A,env_vars=_A):
	A=env_vars
	if A is _A:A={}
	B=subprocess.run(command_list,capture_output=_B,text=_B,cwd=working_dir,env={**A,**os.environ.copy()},check=_D);return B.returncode,B.stdout,B.stderr
def create_archive_from_paths(path_list,base_dir=_A):
	A=io.BytesIO()
	with tarfile.open(fileobj=A,mode='w')as C:
		for B in path_list:D=os.path.relpath(B,start=base_dir);C.add(B,arcname=D)
	A.seek(0);return A
def pong(_):return'PONG!',[]
def run_sbdl(working_dir,argument_list):
	E=working_dir;D='-o';B='';I='-';F='';A='tmp-output-file';G=[I,'']
	def J():
		nonlocal B;E=_D;C=[]
		for A in argument_list:
			if A.strip()==D or A.strip()=='--output':E=_B
			elif E:E=_D;B=A
			elif len(A)>0 and A[0]=='/':C.append(A[1:])
			elif len(A)>2 and A[:3]=='../':C.append(A[3:])
			else:C.append(A)
		return C
	C=[get_config_value(_G)]+J()
	if B in G:C+=[D,'-']
	else:A+=os.path.splitext(B)[1];C+=[D,A]
	K,L,M=exec_external(C,working_dir=E,env_vars={'SBDL_NO_PRETTY':'1'})
	if B not in G:
		H=os.path.join(E,A)
		if os.path.exists(H):
			with open(H,'rb')as N:F=base64.b64encode(N.read()).decode(_E)
	return K,L,M,F
def sbdl_remote(arguments_dict):
	F='command_line';D='data';B=arguments_dict;C=[];A={}
	if F in B and D in B:
		try:
			G=base64.b64decode(B[D])
			with tempfile.TemporaryDirectory()as E:
				with tarfile.open(fileobj=io.BytesIO(G),mode='r')as H:H.extractall(path=E,filter=D);I,J,K,L=run_sbdl(E,B[F]);A['exitcode']=int(I);A['stdout']=J;A['stderr']=K;A['output']=L
		except(base64.binascii.Error,tarfile.TarError,OSError,subprocess.SubprocessError,TypeError,KeyError,AttributeError,IOError,UnicodeDecodeError)as M:C.append(str(M))
	else:C.append('Malformed request (missing entries)')
	return A,C
def handle_request(request_data):
	L='arguments';K='function';J='api_key';I='result';H='api_version';G='api_name';C=request_data;B='errors';time.sleep(get_config_value(_F));A={G:API_NAME,H:API_VERSION,B:[],I:''};M={G,H,J,K,L}
	def D():return len(A[B])==0
	for F in M:
		if F not in C:A[B].append(f"Missing argument: {F}")
	if D()and(C[J]!=get_config_value(_C)or len(get_config_value(_C))==0):A[B].append('Invalid API key')
	if D():
		E=C[K]
		if E in API_FUNCTIONS:N,O=API_FUNCTIONS[E](C[L]);A[B].extend(O);A[I]=N
		else:A[B].append(f"Unrecognized function requested: {E}")
	return D(),A
def handle_request_response(request_data):A,B=handle_request(request_data);response_message(json.dumps(B),A)
def get_json_input(json_string):
	A={}
	try:A=json.loads(json_string)
	except(json.JSONDecodeError,TypeError):pass
	return A
class RestHTTPRequestHandler(BaseHTTPRequestHandler):
	def process_post(C,data):A,B=handle_request(get_json_input(data));return A,json.dumps(B)
	def do_POST(A):B=int(A.headers['Content-Length']);C,D=A.process_post(A.rfile.read(B).decode(_E));A.send_response(200 if C else 400);A.send_header('Content-Type','application/json');A.end_headers();A.wfile.write(D.encode(_E))
def local_server(host,port):A=host,port;B=HTTPServer(A,RestHTTPRequestHandler);print(f"{API_NAME} server {API_VERSION} running on http://{host}:{port}");B.serve_forever()
API_FUNCTIONS.update({'ping':pong,'sbdl-remote':sbdl_remote})
if __name__=='__main__':
	if len(sys.argv)>1:
		if len(sys.argv)!=3:print(f"Format: {os.path.basename(sys.argv[0])} <hostname> <port>");sys.exit(1)
		else:local_server(host=sys.argv[1],port=int(sys.argv[2]))
	else:sys.exit(handle_request_response(get_json_input(sys.stdin.read())))