overview.png: overview.puml
	plantuml -tpng overview.puml


overview.pdf: overview.puml
	plantuml -teps overview.puml
	epstopdf overview.eps


clean:
	rm -f overview.pdf overview.png

