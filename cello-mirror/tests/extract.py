import re,sys
html=open(sys.argv[1]).read()
m=re.search(r'<script type="module">(.*?)</script>',html,re.S)
open(sys.argv[2],'w').write(m.group(1))
