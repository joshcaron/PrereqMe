'use strict';

prereqApp.directive('schoolPicker', ['SchoolService', function(SchoolService) {
	var link = function(scope, element, attrs, ngModel) {
		if (scope.schools === undefined) {
			SchoolService.getSchoolList()
				.then(function(data) {
					scope.schools = data;
					SchoolService.getSavedSchool()
						.then(function(data) {
							scope.selected = _.find(scope.schools, function(school) {
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
					scope.selected = _.find(scope.schools, function(school) {
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
			selected: '=ngModel',
			schools: '=?',
			setCookie: '=?'
		},
		link: link
	};
}]);