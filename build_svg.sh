rm test.csv BOT.svg LYR4.svg LYR3.svg TOP.svg BOARD.svg

python3 allegro2svg.py sample_allegro_cline_data.txt > test.csv 

cat test.csv | grep TOP | awk -F ";" '{print "<path id=\"" $2 "\" d=" $3 " style=\"stroke-width:" $4 "px;stroke:#ff0000;fill:none;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1\" />"}' > TOP.svg
cat test.csv | grep LYR3 | awk -F ";" '{print "<path id=\"" $2 "\" d=" $3 " style=\"stroke-width:" $4 "px;stroke:#ffa500;fill:none;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1\" />"}' > LYR3.svg
cat test.csv | grep LYR4 | awk -F ";" '{print "<path id=\"" $2 "\" d=" $3 " style=\"stroke-width:" $4 "px;stroke:#00ff00;fill:none;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1\" />"}' > LYR4.svg
cat test.csv | grep BOT | awk -F ";" '{print "<path id=\"" $2 "\" d=" $3 " style=\"stroke-width:" $4 "px;stroke:#0000ff;fill:none;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1\" />"}' > BOT.svg

cat svg_header.txt BOT.svg LYR4.svg LYR3.svg TOP.svg svg_footer.txt > BOARD.svg

firefox BOARD.svg &
gnumeric test.csv &

tail test.csv
tail BOARD.svg

