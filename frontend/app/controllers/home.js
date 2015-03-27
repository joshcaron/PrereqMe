'use strict';

prereqApp.controller('HomeController', ['$scope', '$location', 'SchoolService', function($scope, $location, SchoolService) {
	$scope.school = null;

	$scope.schools = [];
	$scope.alerts = [];

	SchoolService.getSchoolList()
		.then(function(data) {
			$scope.schools = data;
		}, function(error) {
			console.error(error);
		});

	$scope.goTo = function(school) {
		if (school !== undefined && school !== null && school != "") {
			$location.path('/schools/' + school.slug + '/');
		} else {
			$scope.addAlert('danger', 'Please choose a valid school.');
		}
	}

	$scope.addAlert = function(type, msg) {
		$scope.alerts.push({type: type, msg: msg});
	}

	$scope.closeAlert = function(index) {
		$scope.alerts.splice(index, 1);
	};
}]);
