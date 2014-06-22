var casper = require('casper').create({
	clientScripts: ["../jquery/jquery-1.11.1.js"]
});
var name = casper.cli.get(0);
var year = casper.cli.get(1);
url = 'http://www.atpworldtour.com/Tennis/Players/Top-Players/' + name + '.aspx?t=mf&y=' + year + '&s=2#';
casper.start(url, function() {
	// this.echo('the heading exists');
	var items = this.evaluate(function() {
		var player_name = $('h1').text();
		var player_stats = {};
		player_stats[player_name] = []
		$('.bioMatchfactsCol').each(function() {
			$(this).find('li').each(function() {
				var number = $(this).find('span').text();
				var label = $(this).clone().find('span').remove().end().text();
				var inner = {};
				inner[label] = number
				player_stats[player_name].push(inner);
			})
		});
		return player_stats;
	});
	this.echo(JSON.stringify(items));
});

casper.run();


