'use strict';

prereqApp.controller('SchoolViewerController', ['$scope', '$location', '$routeParams', 'SchoolService', 'DepartmentService', function($scope, $location, $routeParams, SchoolService, DepartmentService) {
	$scope.school = null;
	$scope.departments = [];
	$scope.showCPS = false;
	$scope.showCoop = false;
	$scope.showInternatl = false;
	$scope.search = "";

	SchoolService.getSchoolBySlug($routeParams.school)
		.then(function(data) {
			$scope.school = data;
			$scope.getDepartments($scope.school);
		}, function(error) {
			console.error(error);
		});

	$scope.getDepartments = function(school) {
		DepartmentService.getDepartmentsForSchool(school)
			.then(function(data) {
				$scope.departments = data;
				$scope.departments.sort(function(a, b) {
					if (a.name > b.name) {
						return 1;
					} else if (a.name < b.name) {
						return -1;
					} else {
						return 0;
					}
				});
			}, function(error) {
				console.error(error);
			});
	}

	$scope.customFilter = function(department) {
		var searchValid =  $scope.search.length > 0;
		var showCPS = !$scope.showCPS && (department.name.search("CPS") > -1);
		var showCoop = !$scope.showCoop && (department.name.search("Coop") > -1);
		var showInternatl = !$scope.showInternatl && (department.name.search("Internat") > -1);
	
		if (searchValid) {
			return department.name.search($scope.search) > -1
			       && !showCPS
			       && !showCoop
			       && !showInternatl;
		} else {
			return !showCPS && !showCoop && !showInternatl;
		}
	}
}]);
