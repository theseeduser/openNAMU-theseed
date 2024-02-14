//윈도우 사이즈에 따라 변경을 할지 않할 지 체크한다.
let isAllowRequestList = true;
let liberty_load_type = 'A';

function liberty_do_func_xss_encode(data) {
    data = data.replace(/'/g, '&#x27;');
    data = data.replace(/"/g, '&quot;');
    data = data.replace(/</g, '&lt;');
    data = data.replace(/</g, '&gt;');

    return data;
}

//매개 변수 parent는 ul태그여야 합니다
function ShowAjaxRecentList(parent) {
	function temp() {
        if(liberty_load_type === 'A') {
            jQuery.ajax({
                url: "/api/recent_change/10", // 호출 URL
                dataType:'json'
            }).done(function(res) {
                let html = "";
                for(let i = 0; i < res.length && i < 10; i++) {
                    let item = res[i];
                    
                    if(item[6] === '') {
                        html += '<li><a class="recent-item" href="/w/' + encodeURIComponent(item[1]) + '" title="' + liberty_do_func_xss_encode(item[1]) +'">';
                        html += "[" + item[2].replace(/^([^ ]+) /, '') + "] ";
                        let text = item[1];
                        if(text.length > 13) {
                            text = text.substr(0, 13);
                            text +="...";
                        }
                        html += liberty_do_func_xss_encode(text);
                        html += "</a></li>";
                    } else {
                        html += "<li>[---] ---</li>";
                    }
                }
                
                if(parent != null) {
                    jQuery(parent).html(html);
                }
            });
        } else {
            jQuery.ajax({
                url: "/api/recent_discuss/10", // 호출 URL
                dataType:'json'
            }).done(function(res) {
                let html = "";
                for(let i = 0; i < res.length && i < 10; i++) {
                    let item = res[i];

                    html += '<li><a class="recent-item" href="/thread/' + encodeURIComponent(item[3]) + '" title="' + liberty_do_func_xss_encode(item[1]) +'">';
                    html += "[" + item[2].replace(/^([^ ]+) /, '') + "] ";
                    let text = item[1];
                    if(text.length > 13) {
                        text = text.substr(0, 13);
                        text +="...";
                    }
                    html += liberty_do_func_xss_encode(text);
                    html += "</a></li>";
                }
                
                if(parent != null) {
                    jQuery(parent).html(html);
                }
            });
        }
	}
	temp();
}

function liberty_side_load(get_type) {
    liberty_load_type = get_type;
    if(get_type === 'A') {
        $( this ).addClass( 'active' );
		$( '#liberty-recent-tab2' ).removeClass( 'active' );
        
        document.getElementById('liberty_recent_link').href = "/recent_changes";
    } else {
        $( this ).addClass( 'active' );
		$( '#liberty-recent-tab1' ).removeClass( 'active' );
        
        document.getElementById('liberty_recent_link').href = "/recent_discuss"
    }
    
    ShowAjaxRecentList(jQuery("#live-recent-list"));
}

/**
 * Vector-specific scripts
 */
var recentIntervalHandle = null;
jQuery( function ( jQuery ) {
	var width = jQuery(window).width();
	if(width > 1023) {
		isAllowRequestList = true;
		ShowAjaxRecentList(jQuery("#live-recent-list"));
	}
	else {
		isAllowRequestList = false;
	}

	//만약에 화면의 사이즈가 작아 최근 변경글이 안보일 시, 갱신을 하지 않는다.
	jQuery(window).resize(recentIntervalCheck);
});

var recentIntervalCheck = function() {
	var width = jQuery(window).width();
	if(width <= 1023) {
		if(recentIntervalHandle != null) {
			clearInterval(recentIntervalHandle);
			recentIntervalHandle = null;
		}
		isAllowRequestList = false;
	} else {
		if(recentIntervalHandle == null) {
			recentIntervalHandle = setInterval(function() {
				ShowAjaxRecentList(jQuery("#live-recent-list"));
			}, 60 * 1000);
		}
		isAllowRequestList = true;
	}
}

jQuery(document).ready(function(jQuery) {
	recentIntervalCheck();
});

$( function () {
	'use strict';
	/* Dropdown fade in */
	$( '.dropdown' ).on( 'show.bs.dropdown', function () {
		$( this ).find( '.dropdown-menu' ).first().stop( true, true ).fadeToggle( 200 );
	} );

	$( '.dropdown' ).on( 'hide.bs.dropdown', function () {
		$( this ).find( '.dropdown-menu' ).first().stop( true, true ).fadeToggle( 200 );
	} );

	$( '.btn-group' ).on( 'show.bs.dropdown', function () {
		$( this ).find( '.dropdown-menu' ).first().stop( true, true ).fadeToggle( 200 );
	} );

	$( '.btn-group' ).on( 'hide.bs.dropdown', function () {
		$( this ).find( '.dropdown-menu' ).first().stop( true, true ).fadeToggle( 200 );
	} );
	/* Dropdown fade in End */
} );