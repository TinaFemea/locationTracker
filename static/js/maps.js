var map;
var bounds;

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
    var loc = currLocs.getLoc(uuid);

	if (!loc) return;

	if (!loc.marker) {
		addMarker(loc);
	}
	
	startBounce(loc.marker);

	setTimeout(stopBounce.bind(null, loc.marker), 1000);
}

var maxMarkers = 25;

var currLocs = {
	dataList: [],

	clear: function() {
		this.dataList.forEach(function(item) {
			removeMarker(item);
 		});

 		
 		$("#data tbody").html("");
 		this.dataList = [];
	},

	add: function(oneLoc) {
		this.dataList.push(oneLoc);
	},

	getLoc: function(uuid) {
		for (var i =0; i < this.dataList.length; i++) {
			if (this.dataList[i].uuid == uuid) {
				return this.dataList[i];
			}
		};
		return null;
	},

	countMarkers: function() {
		var counter = 0;
		this.dataList.forEach(function(item) {
			if (item.marker) counter = counter + 1;
		});
		return counter;
	},

	lastPoint: function() {
		if (this.dataList && this.dataList.length > 0) {
			return this.dataList[this.dataList.length-1].timestamp;
		} else {
			return 0;
		}
	},

 	handleNewData: function(allTheLocs) {
		if (allTheLocs == undefined || allTheLocs.length == 0) return;

	 	allTheLocs.sort(compare);

 		for (var i =0; i < allTheLocs.length; i++) {
			this.add(allTheLocs[i]);
			addNew(allTheLocs[i]);
 		};

 		if (this.countMarkers() > maxMarkers * 1.5) {
 			this.rebalanceMarkers();
 		}

 	},

 	rebalanceMarkers: function() {
 		var howManyPointsBetween = Math.round(this.dataList.length / maxMarkers);

		for (var i =0; i < this.dataList.length; i++) {
			var needsMarker = ((i % howManyPointsBetween) == 0);
			if (this.dataList[i].marker && !needsMarker) {
				removeMarker(this.dataList[i]);
			} else if (!this.dataList[i].marker && needsMarker) {
				addMarker(this.dataList[i]);
			}
		};
		
 	}
}


function initMap() {
    $("#filterTime option:last").attr("selected", "selected");

    $( "select" ).change(function() {
		if (currLocs) currLocs.clear();
	});
    update();
}

function pad(num, size) {
    var s = "000" + num;
    return s.substr(s.length-size);
}

var lastStartPoint = [0, 0]
var lastSPMarker

function addStartingPoint(startingPoint) {
	if (!map)
		return;

	if (lastStartPoint[0] == startingPoint[0] && 
		lastStartPoint[0] == startingPoint[0]) {
		return;
	}

	if (lastSPMarker)
		lastSPMarker.setMap(null);

	lastStartPoint[0] = startingPoint[0];
	lastStartPoint[1] = startingPoint[1];
	
	var position = {lat: Number(startingPoint[0]), lng: Number(startingPoint[1])};

	var icon = {
        url: "flag.svg",
        scaledSize: new google.maps.Size(50,50)
    }

	lastSPMarker = new google.maps.Marker({
	  position: position,
	  map: map,
	  icon: icon,
	  title: "start point",

	});
}

function addNew(currLoc) {
	
	if (!map) {
		var position = {lat: Number(currLoc.latitude), lng: Number(currLoc.longitude)};
		map = new google.maps.Map(document.getElementById('map'), {
					zoom: 15,
					center: position});
		bounds = new google.maps.LatLngBounds()
	}

	ppTime = new Date(currLoc.timestamp);
	//This is UTC!
	ppDateString = 	pad(ppTime.getFullYear(), 4) + "-" + 
					pad(ppTime.getMonth() + 1, 2) + "-" +
					pad(ppTime.getDate(), 2)
					
	ppTimeString =	pad(ppTime.getHours(), 2) + ":" + 
					pad(ppTime.getMinutes(), 2) + ":" +
					pad(ppTime.getSeconds(), 2) + "." + 
					pad(ppTime.getMilliseconds(), 3);

	currLoc.tr = $('<tr>').attr("id",currLoc.uuid).append(
            $('<td onclick="handleClick(event);">').html(currLoc.latitude + "<br>" + currLoc.longitude),
            $('<td>').html(ppDateString + "<br>" + ppTimeString),
            $('<td>').html(Number(currLoc.timeDelta).toFixed(3).toString() + " sec" + "<br>" + Number(currLoc.startDelta).toFixed(3).toString() + " m" ),
            $('<td>').html(currLoc.lap)
        );

    $("#data tbody").append(currLoc.tr);
	
	//	add the marker
	addMarker(currLoc);
	
    optionSelector = '#filterTime option[value="' + ppDateString + '"]';
    if ($(optionSelector).length == 0) {
    	$('#filterTime').append($('<option>').attr('value', ppDateString).text(ppDateString));
    }

	lapOptionSelector = '#filterLap option[value="' + currLoc.lap + '"]';
    if ($(lapOptionSelector).length == 0) {
    	$('#filterLap').append($('<option>').attr('value', currLoc.lap).text(currLoc.lap));
    }
}
function addMarker(currLoc) {
	var position = {lat: Number(currLoc.latitude), lng: Number(currLoc.longitude)};

	currLoc.marker = new google.maps.Marker({
	  position: position,
	  map: map,
	  title: ppTimeString
	});

	currLoc.tr.addClass("table-secondary");

    //	Fix the map bounds
    bounds.extend(currLoc.marker.getPosition());
	map.fitBounds(bounds);
}

function removeMarker(currLoc) {
	if (currLoc.marker)	{
		currLoc.marker.setMap(null);
		currLoc.marker = null;
		currLoc.tr.removeClass("table-secondary");
	}
}

function update() {
	var lastPoint = currLocs.lastPoint();
	var queryParams = "after=" + lastPoint +
						"&filterDate=" + $('#filterTime').val() +
						"&filterLap=" + $('#filterLap :selected').text();

	$.ajax({url: "\locations?" + queryParams, context: document.body}).done(function(data) {
		results = data.results
		currLocs.handleNewData(results);
		addStartingPoint(data.startPoint);
		setTimeout(function(){ update(); }, 1000);
	})
}
