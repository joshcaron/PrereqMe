'use strict';

prereqApp.controller('CourseController', ['$scope', '$location', '$routeParams', 'SchoolService', 'DepartmentService', 'CourseService', function($scope, $location, $routeParams, SchoolService, DepartmentService, CourseService) {
	$scope.school = null;
	$scope.department = null;
	$scope.courses = null;

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
				$scope.getCourse($scope.school, $scope.department, $routeParams.course);
			}, function(error) {
				console.error(error);
			});
	};

	$scope.getCourse = function(school, department, number) {
		CourseService.getCourse(school, department, number)
			.then(function(data) {
				$scope.course = data;
			}, function(error) {
				console.error(error);
			});
	};
}]);
