'use strict';
module.exports = function(grunt) {

  grunt.initConfig({
    sass: {
      dist: {
        options: {
          style: 'compressed',
          compass: false,
          sourcemap: false
        },
        files: {
          '../webassets/css/datavic_odp_theme.css': [
            'sass/styles.scss'
          ]
        }
      }
    },
    watch: {
      sass: {
        files: [
          'sass/**/*.scss'
        ],
        tasks: ['sass']
      }
    },
    cssmin: {
        css: {
            src: '../webassets/css/datavic_odp_theme.css',
            dest: '../webassets/css/datavic_odp_theme.css'
        }
    }
  });

  // Load tasks
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-contrib-cssmin');

  grunt.registerTask('default', [
    'sass',
    'cssmin'
  ]);

  grunt.registerTask('dev', [
    'watch'
  ]);

};
