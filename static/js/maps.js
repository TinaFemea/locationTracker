var map;

function initMap() {
    update();
}

function update() {
	$.ajax({url: "\locations", context: document.body}).done(function(data) {
		addMarkers(data);
		sidebar(data);
	});
}

function addMarkers(data) {
	for(var i = 0; i < data.length; i++) {
		var position = {lat: Number(data[i].latitude), lng: Number(data[i].longitude)};
		
		if (!map) {
			map = new google.maps.Map(document.getElementById('map'), {
						zoom: 15,
						center: position});
		}

		var marker = new google.maps.Marker({
		  position: position,
		  map: map,
		  title: 'Hello World! - ' + i
		});
	}
}

function sidebar(data) {
	var body = $("#data tbody");

	for(var i = 0; i < data.length; i++) {
		var tr = $('<tr>').append(
            $('<td>').text(data[i].latitude),
            $('<td>').text(data[i].longitude),
            $('<td>').text(data[i].timestamp)
        );
     	body.append(tr);
     }
}
