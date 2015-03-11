'use strict';

prereqApp.controller('SchoolDepartmentController', ['$scope', '$location', '$routeParams', 'SchoolService', 'DepartmentService', function($scope, $location, $routeParams, SchoolService, DepartmentService) {
	$scope.school = null;
	$scope.department = null;
	$scope.courses = [];

	SchoolService.getSchoolBySlug($routeParams.school)
		.then(function(data) {
			$scope.school = data;
			$scope.getDepartment($scope.school, $routeParams.department);
		}, function(error) {
			console.error(error);
		});

	$scope.getDepartment = function(school, department) {
		DepartmentService.getDepartment(school, department)
			.then(function(data) {
				$scope.department = data;
			}, function(error) {
				console.error(error);
			});
	}
}]);
