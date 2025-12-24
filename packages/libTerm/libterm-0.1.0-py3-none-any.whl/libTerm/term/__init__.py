#!/usr/bin/env python
import os
if os.name == 'nt':
	from libTerm.term.winnt import Term
else:
	from libTerm.term.posix import Term