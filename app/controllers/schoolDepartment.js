'use strict';

prereqApp.controller('SchoolDepartmentController', ['$scope', '$location', '$routeParams', 'SchoolService', 'DepartmentService', 'CourseService', function($scope, $location, $routeParams, SchoolService, DepartmentService, CourseService) {
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
				$scope.courses = $scope.getCourses($scope.school, $scope.department);
			}, function(error) {
				console.error(error);
			});
	};

	$scope.getCourses = function(school, department) {
		CourseService.getAllCourses(school, department)
			.then(function(data) {
				$scope.courses = data;
				$scope.courses.sort(function(a, b) {
					return a.number - b.number;
				});
			}, function(error) {
				console.error(error);
			});
	};
}]);
