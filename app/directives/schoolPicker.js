'use strict';

prereqApp.directive('schoolPicker', ['SchoolService', function(SchoolService) {
	var setCookie = function() {

	}

	var link = function(scope, element, attrs) {
		if (scope.list === undefined) {
			SchoolService.getSchoolList()
				.then(function(data) {
					scope.list = data;

					SchoolService.getSavedSchool()
						.then(function(data) {
							scope.selected = _.find(scope.list, function(school) {
								return school.id == data.id;
							});
						}, function(error) {
							console.log(error);
						});
				}, function(error) {
					console.error(error);
				});
		} else {
			SchoolService.getSavedSchool()
				.then(function(data) {
					scope.selected = _.find(scope.list, function(school) {
						return school.id == data.id;
					});
				}, function(error) {
					console.log(error);
				});
		}


		scope.saveSchool = function(school) {
			SchoolService.setSavedSchool(school, scope.setCookie);
		};
	};

	return {
		restrict: 'E',
		templateUrl: 'templates/schoolPicker.html',
		scope: {
			list: '=?schools',
			change: '=onChange',
			selected: '=ngModel',
			allowEmpty: '=?',
			setCookie: '=?'
		},
		link: link
	};
}]);