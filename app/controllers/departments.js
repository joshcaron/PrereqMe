'use strict';


prereqApp.controller('DepartmentsController', ['$scope', 'SchoolService', 'DepartmentService', function($scope, SchoolService, DepartmentService) {
	$scope.selectedSchool = null;
	$scope.departments = [];
	SchoolService.getSavedSchool()
		.then(function(data) {
			$scope.selectedSchool = data;

			DepartmentService.getDepartmentsForSchool($scope.selectedSchool)
				.then(function(data) {
					$scope.departments = data;
				}, function(error) {
					console.error(error);
				});
		}, function(error) {
			console.error(error);
		});
}]);
