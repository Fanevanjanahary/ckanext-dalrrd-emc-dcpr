"use strict";


ckan.module('emc-factes-avtive', function (jQuery, _) {

    function getUrlParameter(param) {
          let sPageURL = window.location.search.substring(1),
                URLVariables = sPageURL.split('&'),
                sParameterName,
                i;

            for (i = 0; i < URLVariables.length; i++) {
                sParameterName = URLVariables[i].split('=');

                if (sParameterName[0] === param) {
                    return sParameterName[1];
                }
            }
            return false;
    }

    return {
        initialize: function () {

            const filters = {
                'organization': 'Organizations',
                'vocab_sasdi_themes': 'SASDITheme',
                'vocab_iso_topic_categories': 'ISOTopicCategory',
                'tags': 'Tags'
            };
            const keys = Object.keys(filters);

            for(let i=0; i<keys.length; i++){
                if(getUrlParameter(keys[i])){
               document.getElementById(filters[keys[i]]).classList.add("in")
           }
       }
        }
    }

})

// =====================
/**
    as the dcpr_request has a public page,
    facet only need to change the window
    location to the dcpr requests public
    page.
*/

ckan.module("dcpr_request_facet", function($){
    return{
        initialize:function(){
            $.proxyAll(this,/_on/);
            this.el.on("click", this._onClick)
        },

        _onClick:function(){
            let text = this.el.text()
            if(text.toLowerCase().indexOf("dcpr request") != -1){
               // window.location.href = window.location.origin + '/dcpr/'
            }
        }
    }
})
