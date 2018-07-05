var map;

function compare(a,b) {
  if (Number(a.timestamp) < Number(b.timestamp))
    return -1;
  if (Number(a.timestamp) > Number(b.timestamp))
    return 1;
  return 0;
}

function startBounce(marker) {
    marker.setAnimation(google.maps.Animation.BOUNCE);
}

function stopBounce(marker) {
    marker.setAnimation(null);
}

function handleClick(e){
    var uuid = $(e.currentTarget).parent().attr("id");
    var marker = currLocs.getMarker(uuid);

	startBounce(marker);

	setTimeout(stopBounce.bind(null, marker), 1000);
}

var currLocs = {
	dataList: [],

	add: function(oneLoc) {
		this.dataList[oneLoc.uuid] = oneLoc;
	},

	contains: function(uuid) {
		return (uuid in this.dataList);
	},

	getMarker: function(uuid) {
		return this.dataList[uuid].marker;
	},



 	handleNewData: function(allTheLocs) {
 		var oldUUIDs = [];
		
		if (allTheLocs == undefined || allTheLocs.length == 0) return;

	 	allTheLocs.sort(compare);

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

function pad(num, size) {
    var s = "000" + num;
    return s.substr(s.length-size);
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


	ppTime = new Date(currLoc.timestamp);
	//This is UTC!
	ppTimeString = 	pad(ppTime.getDate(), 2) + "-" +
					pad(ppTime.getMonth(), 2) + "-" +
					pad(ppTime.getFullYear(), 4) + "<br>" +

					pad(ppTime.getHours(), 2) + ":" + 
					pad(ppTime.getMinutes(), 2) + ":" +
					pad(ppTime.getSeconds(), 2) + "." + 
					pad(ppTime.getMilliseconds(), 3);

	currLoc.tr = $('<tr>').attr("id",currLoc.uuid).append(
            $('<td onclick="handleClick(event);">').html(currLoc.latitude + "<br>" + currLoc.longitude) ,
            $('<td>').html(ppTimeString),
            $('<td>').html(Number(currLoc.timeDelta).toFixed(3).toString() + " sec" + "<br>" + Number(currLoc.spaceDelta).toFixed(3).toString() + " m" ),
          
        );

    $("#data tbody").append(currLoc.tr);
}

function removeStale(currLoc) {
	currLoc.marker.setMap(null);
	currLoc.tr.remove();
}

function update() {
	$.ajax({url: "\locations", context: document.body}).done(function(data) {
		data = JSON.parse(data);
		currLocs.handleNewData(data);

		setTimeout(update(), 500);
	});
}
