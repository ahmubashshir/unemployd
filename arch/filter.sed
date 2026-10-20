# process only if first line
1{
	s/-.*$// # discard after first hyphen
	p # print
}
d # consume everything
