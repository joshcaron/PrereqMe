'use strict';

prereqApp.controller('SchoolsController', ['$scope', '$location', 'SchoolService', function($scope, $location, SchoolService) {
	$scope.selectedSchool = null;
	$scope.goToDepartments = function(school) {
		if (school == null) {
			console.log("Can't go to departments.");
		} else {
			$location.path('/schools/' + school.slug + '/departments');
		}
	};
}]);
