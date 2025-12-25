#!/usr/bin/python3
_I='remark'
_H='pragma'
_G='child'
_F='parent'
_E='aspect'
_D='description'
_C='identifier'
_B=None
_A=' '
import argparse,csv,re,sys,sbdl
__NAME='cs2sbdl'
__VERSION='0.2.3'
def null_handler(content):return sbdl.SBDL_Parser.sanitize(content)
def doors_link_san(content):
	B=content;A=B;C='{LINK';D='}';F=C+'.*?'+D
	def G(link_string_body):
		E='NO_LINK_NAME';A=link_string_body[len(C):-len(D)].strip();A=A.split('=')
		for B in range(len(A)):
			if A[B].endswith('title')and len(A)>B+1:E=A[B+1][1:-5]+_A;break
		return E
	for E in re.finditer(F,B):H=G(E.group());A=A.replace(E.group(),H)
	return A
def null_handler_doors(content):return null_handler(doors_link_san(content))
def id_handler(content):return null_handler('_'.join(content.split()))
def doors_req_id_san(content):return id_handler(content.rstrip('.'))
def doors_parent_child_id_san(content):
	B=content.splitlines();A=''
	try:
		C=[]
		for D in B:C.append(D.split()[1])
		A=sbdl.SBDL_Parser.Attributes.separator.join(C)
	except Exception as E:A=sbdl.SBDL_Parser.Attributes.separator.join(B)
	return null_handler(A)
column_handlers={_C:id_handler,_E:id_handler,_D:null_handler,_F:id_handler,_G:id_handler,_H:null_handler,_I:null_handler}
column_handlers_doors={_C:doors_req_id_san,_E:id_handler,_D:null_handler_doors,_F:doors_parent_child_id_san,_G:doors_parent_child_id_san,_H:null_handler_doors,_I:null_handler_doors}
def csv2sbdl(table,id_col,aspect_col,desc_col,remark_col,parent_col,child_col,pragma_col,element_type,write_aspect_placeholders,column_handlers=column_handlers):
	W='{description}';M=pragma_col;L=child_col;K=parent_col;J=remark_col;I=desc_col;H=aspect_col;G=id_col;B=column_handlers;E=[];N={};A=sbdl.SBDL_Parser.Tokens;O=sbdl.SBDL_Parser.Types;D=sbdl.SBDL_Parser.Attributes;X='custom:extended';Y='{rid} '+A.declaration+_A+element_type+_A+A.declaration_group_delimeters[0].replace('{','{{')+_A+D.description+A.declaration_attribute_assign+A.declaration_attribute_delimeter+W+A.declaration_attribute_delimeter+_A+X+A.declaration_attribute_assign+A.declaration_attribute_delimeter+'{remark}'+A.declaration_attribute_delimeter+_A+O.aspect+A.declaration_attribute_assign+A.declaration_attribute_delimeter+'{aspect}'+A.declaration_attribute_delimeter+_A+D.parent+A.declaration_attribute_assign+A.declaration_attribute_delimeter+'{parent}'+A.declaration_attribute_delimeter+_A+D.child+A.declaration_attribute_assign+A.declaration_attribute_delimeter+'{child}'+A.declaration_attribute_delimeter+_A+D.pragma+A.declaration_attribute_assign+A.declaration_attribute_delimeter+'{pragma}'+A.declaration_attribute_delimeter+_A+A.declaration_group_delimeters[1].replace('}','}}');Z='{aid} '+A.declaration+_A+O.aspect+_A+A.declaration_group_delimeters[0].replace('{','{{')+_A+D.description+A.declaration_attribute_assign+A.declaration_attribute_delimeter+W+A.declaration_attribute_delimeter+_A+A.declaration_group_delimeters[1].replace('}','}}')
	for C in table:
		P='';F='';Q='';R='';S='';T='';U=''
		if G!=_B:P=B[_C](C[int(G)])
		if H!=_B:
			F=B[_E](C[int(H)])
			for a in F.split(sbdl.SBDL_Parser.Attributes.separator):N[a]=True
		if I!=_B:Q=B[_D](C[int(I)])
		if J!=_B:U=B[_I](C[int(J)])
		if K!=_B:R=B[_F](C[int(K)])
		if L!=_B:S=B[_G](C[int(L)])
		if M!=_B:T=B[_H](C[int(M)])
		b=Y.format(rid=P,description=Q,remark=U,aspect=F,parent=R,child=S,pragma=T);E.append(b)
	if write_aspect_placeholders:
		for V in N:c=Z.format(aid=B[_C](V),description=B[_D](V));E.append(c)
	return E
def main(arguments):
	A=arguments;F=0;C=[]
	for G in A.source_files:
		with open(G,'r')as H:
			I=csv.reader(H,delimiter=A.delimiter);B=[A for A in I]
			if A.skipheader:B=B[1:]
			D=column_handlers
			if A.doors:D=column_handlers_doors
			C.extend(csv2sbdl(B,A.identifier,A.aspect,A.description,A.extended,A.parent,A.child,A.pragma,A.sbdl_type,A.placeholder_aspects,D))
	with sbdl.open_output_file(A.output,append=A.append)as E:
		if not A.append:E.write('#!sbdl\n')
		for J in C:E.write(J+'\n')
	return F
def handle_arguments(args_l):C=False;B='store_true';A=argparse.ArgumentParser(description='{} Version {}. Convert a CSV sheet into SBDL. Author: michael@mahicks.org.'.format(__NAME.upper(),__VERSION),epilog='e.g. "'+sys.argv[0]+' <file 1> <file 2> <file n>"',formatter_class=argparse.ArgumentDefaultsHelpFormatter);A.add_argument('source_files',help='List of files to compile',nargs='+');A.add_argument('--identifier',help="Column containing element's identifier",default=_B);A.add_argument('--aspect',help="Column containing element's aspect",default=_B);A.add_argument('--description',help="Column containing element's description",default=_B);A.add_argument('--parent',help="Column containing element's parent identifiers",default=_B);A.add_argument('--child',help="Column containing element's child identifiers",default=_B);A.add_argument('--extended',help="Column containing element's extended information",default=_B);A.add_argument('--pragma',help="Column containing element's pragma content",default=_B);A.add_argument('--skipheader',help='Treat the first line as header (and skip it)',action=B,default=C);A.add_argument('--doors',help='Treat the CSV data as having been exported from DOORS',action=B,default=C);A.add_argument('--placeholder_aspects',help='Write placeholder aspects into output SBDL',action=B,default=C);A.add_argument('-o','--output',help='Specify the name of the output file',default='output.sbdl');A.add_argument('-a','--append',help='Append to the output file instead of truncating it',action=B,default=C);A.add_argument('--delimiter',help='CSV column delimiter',default=',');A.add_argument('--sbdl_type',help='SBDL Element-type for generated ouptut',default=sbdl.SBDL_Parser.Types.requirement);return A.parse_args(args_l)
if __name__=='__main__':sys.exit(main(handle_arguments(sys.argv[1:])))