var map;
var currLocs = {
	dataList: [],

	add: function(oneLoc) {
		this.dataList[oneLoc.uuid] = oneLoc;
	},

	contains: function(uuid) {
		return (uuid in this.dataList);
	},

 	handleNewData: function(allTheLocs) {
 		var oldUUIDs = [];

 		for (var i = 0; i < Object.keys(this.dataList).length; i++) {
 			oldUUIDs[Object.keys(this.dataList)[i]] = 0;
 		}

 		for (var i = 0; i < allTheLocs.length; i++) {
 			if (this.contains(allTheLocs[i].uuid)) {
 				oldUUIDs[allTheLocs[i].uuid] = 1;
 			} else {
 				this.add(allTheLocs[i]);
 				addNew(allTheLocs[i]);
 			}
 		}

 		for(var i = 0; i < Object.keys(oldUUIDs).length; i++) {
 			var key = Object.keys(oldUUIDs)[i];
 			if (oldUUIDs[key] == 0) {
 				removeStale(this.dataList[key]);
 				delete this.dataList[key];
 			}
 		}
 	}	
}



function initMap() {
    update();
}

function addNew(currLoc) {
	var position = {lat: Number(currLoc.latitude), lng: Number(currLoc.longitude)};

	if (!map) {
		map = new google.maps.Map(document.getElementById('map'), {
					zoom: 15,
					center: position});
	}

	currLoc.marker = new google.maps.Marker({
	  position: position,
	  map: map,
	  title: currLoc.uuid
	});

	currLoc.tr = $('<tr>').append(
            $('<td>').text(currLoc.latitude),
            $('<td>').text(currLoc.longitude),
            $('<td>').text(currLoc.timestamp)
        );
    $("#data tbody").append(currLoc.tr);
}

function removeStale(currLoc) {
	currLoc.marker.setMap(null);
	currLoc.tr.remove();
}

function update() {
	$.ajax({url: "\locations", context: document.body}).done(function(data) {
		currLocs.handleNewData(data);

		setTimeout(update(), 500);
	});

}