<?xml version="1.0" encoding="UTF-8"?>

<!-- ====================================================================
     変換対象書類名：特実審査周辺（共通部）
     ====================================================================-->
<xsl:stylesheet version="3.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:jp="http://www.jpo.go.jp"
                exclude-result-prefixes="jp">
    
  <!-- this xslt was created with reference to v4xva_ntc-pt-e.xsl
       of Internet Application Software version i5.30 provided by JPO -->
     
    <xsl:variable name="node" select="name(//jp:notice-pat-exam/*)" />
    
    <xsl:include href="ntc-ninsyo.xsl" />
    <xsl:include href="v4xva_prm.xsl" />
    <xsl:include href="dispatch-control-article.xsl" />
    <xsl:include href="helpers.xsl" />
    
    <!-- lookup <images> in source xml -->
    <xsl:key name="image-table" match="images/image[@size_tag='large']" use="@orig" />
    
    <!-- ====================================================================
         jp:notice-pat-exam
         ====================================================================-->
    <xsl:template match="jp:notice-pat-exam">
        <xsl:apply-templates
            select="jp:decision-of-registration-a01 | jp:decision-of-rejection-a02
                | jp:notice-of-rejection-a131 | jp:declining-the-amendment-a191
                | jp:declining-the-amendment-a192 | jp:examiner-notification-a251
                | jp:examiner-notification-a2514 | jp:examiner-notification-a2515
                | jp:examiner-notification-a2516 | jp:examiner-notification-a252
                | jp:examiner-notification-a2522 | jp:examiner-notification-a2529
                | jp:examiner-notification-a30
                | jp:examiner-notification-a25110| jp:examiner-notification-a25111" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:decision-of-registration-a01
         ====================================================================-->
    <xsl:template match="jp:decision-of-registration-a01">
        <xsl:apply-templates select="jp:document-name" />
        <xsl:apply-templates select="jp:kind-of-application" />
        <xsl:apply-templates select="jp:bibliog-in-ntc-pat-exam" />
        <xsl:apply-templates select="jp:reconsideration-before-appeal" />
        <xsl:apply-templates select="jp:conclusion-part-article" />
        <xsl:apply-templates select="jp:drafting-body" />
        <xsl:apply-templates select="jp:footer-article" />
        <xsl:apply-templates select="jp:final-decision-group" />
        <xsl:apply-templates select="jp:final-decision-memo" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:decision-of-rejection-a02
         ====================================================================-->
    <xsl:template match="jp:decision-of-rejection-a02">
        <xsl:apply-templates select="jp:document-name" />
        <xsl:apply-templates select="jp:bibliog-in-ntc-pat-exam" />
        <xsl:apply-templates select="jp:reconsideration-before-appeal" />
        <xsl:apply-templates select="jp:drafting-body" />
        <xsl:apply-templates select="jp:footer-article" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:notice-of-rejection-a131 | jp:declining-the-amendment-a191 |
         jp:declining-the-amendment-a192 | jp:examiner-notification-a251 |
         jp:examiner-notification-a2514 | jp:examiner-notification-a2515 |
         jp:examiner-notification-a2516 | jp:examiner-notification-a252 |
         jp:examiner-notification-a2522 | jp:examiner-notification-a2529 |
         jp:examiner-notification-a25110 | jp:examiner-notification-a25111
         ====================================================================-->
    <xsl:template
        match="jp:notice-of-rejection-a131 | jp:declining-the-amendment-a191
            | jp:declining-the-amendment-a192 | jp:examiner-notification-a251
            | jp:examiner-notification-a2514 | jp:examiner-notification-a2515
            | jp:examiner-notification-a2516 | jp:examiner-notification-a252
            | jp:examiner-notification-a2522 | jp:examiner-notification-a2529
            | jp:examiner-notification-a25110 | jp:examiner-notification-a25111">
        <xsl:apply-templates select="jp:document-name" />
        <xsl:apply-templates select="jp:bibliog-in-ntc-pat-exam" />
        <xsl:apply-templates select="jp:reconsideration-before-appeal" />
        <xsl:apply-templates select="jp:conclusion-part-article" />
        <xsl:apply-templates select="jp:drafting-body" />
        <xsl:apply-templates select="jp:footer-article" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:examiner-notification-a30
         ====================================================================-->
    <xsl:template match="jp:examiner-notification-a30">
        <xsl:apply-templates select="jp:document-name" />
        <xsl:apply-templates select="jp:bibliog-in-ntc-pat-exam" />
        <xsl:apply-templates select="jp:reconsideration-before-appeal" />
        <xsl:apply-templates select="jp:image-group" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:document-name
         ====================================================================-->
    <!-- 書類名 -->
    <xsl:template match="jp:document-name">
        <xsl:choose>
            <xsl:when test="./@jp:error-code">
                <xsl:value-of select="." />
            </xsl:when>
            <xsl:otherwise>
                <xsl:element name="div">
                    <xsl:attribute name="class">document-title</xsl:attribute>
                    <xsl:value-of select="." />
                </xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         jp:kind-of-application
         ====================================================================-->
    <!-- 出願種別 -->
    <xsl:template match="jp:kind-of-application">
        
        <xsl:choose>
            <xsl:when test="ancestor::jp:final-decision-group">
                <xsl:element name="div">
                    <xsl:value-of select="'１．出願種別　　　　　　　　' || ." />
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:element name="div">
                    <xsl:attribute name="class" select="kind-of-application"/>
                    <xsl:value-of select="'（' || . || '）'" />
                </xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         jp:bibliog-in-ntc-pat-exam
         ====================================================================-->
    <!-- 書誌部 -->
    <xsl:template match="jp:bibliog-in-ntc-pat-exam">
        <xsl:element name="div">
            <xsl:attribute name="class">bibliog</xsl:attribute>
            
            <xsl:element name="div">
                <xsl:apply-templates select="jp:application-reference" />
            </xsl:element>
            
            <xsl:element name="div">
                <xsl:apply-templates select="jp:drafting-date" />
            </xsl:element>
            
            <xsl:element name="div">
                <xsl:apply-templates select="jp:draft-person-group" />
            </xsl:element>
            
            <xsl:element name="div">
                <xsl:apply-templates select="invention-title" />
            </xsl:element>
            
            <xsl:element name="div">
                <xsl:apply-templates select="jp:number-of-claim" />
            </xsl:element>
            
            <xsl:for-each select="jp:addressed-to-person-group">
                <xsl:element name="div">
                    <xsl:apply-templates select="." />
                </xsl:element>
            </xsl:for-each>
            
            <xsl:apply-templates select="jp:publication" />
            <xsl:element name="div">
                <xsl:apply-templates select="jp:article-group" />
                <xsl:apply-templates select="jp:remark" />
            </xsl:element>
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:image-group
         ====================================================================-->
    <!-- イメージ -->
    <xsl:template match="jp:image-group">
        <xsl:apply-templates select="img" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:reconsideration-before-appeal
         ====================================================================-->
    <!-- 前置審査 -->
    <xsl:template match="jp:reconsideration-before-appeal">
        <xsl:if test="./@jp:true-or-false = 'true'">
            <xsl:element name="div">
                <xsl:value-of select="'［前置審査］'" />
            </xsl:element>
            
            <xsl:if test="ancestor::jp:decision-of-registration-a01">
                <xsl:element name="div">
                    <xsl:value-of select="'　原査定を取消す。'" />
                </xsl:element>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    
    <!-- ====================================================================
         jp:conclusion-part-article
         ====================================================================-->
    <!-- 結論 -->
    <xsl:template match="jp:conclusion-part-article">
        <xsl:element name="div">
            <xsl:attribute name="class">conclusion-part-article</xsl:attribute>
            <xsl:for-each select="p">
                <xsl:apply-templates select="." />
            </xsl:for-each>
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:drafting-body
         ====================================================================-->
    <!-- 本文部 -->
    <xsl:template match="jp:drafting-body">
        <xsl:element name="div">
            <xsl:attribute name="class">drafting-body</xsl:attribute>
            <xsl:apply-templates select="p | jp:heading" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:footer-article
         ====================================================================-->
    <!-- フッタ部 -->
    <xsl:template match="jp:footer-article">
        <xsl:element name="div">
            <xsl:apply-templates select="jp:administrative-appeal-sentence" />
            <xsl:apply-templates select="jp:approval-column-article" />
            <xsl:apply-templates select="jp:approval-without-contents" />
            <xsl:apply-templates select="jp:certification-column-article" />
            <xsl:apply-templates select="jp:inquiry-article" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:final-decision-group
         ====================================================================-->
    <!-- 査定固有部 -->
    <xsl:template match="jp:final-decision-group">
        <xsl:apply-templates select="jp:kind-of-application" />
        <xsl:apply-templates select="jp:exist-of-reference-doc" />
        <xsl:apply-templates select="jp:patent-law-section30" />
        <xsl:apply-templates select="jp:change-flag-invention-title" />
        <xsl:apply-templates select="jp:ipc-article" />
        <xsl:apply-templates select="jp:classification-article" />
        <xsl:apply-templates select="jp:deposit-article" />
        <xsl:apply-templates select="jp:parent-application-article" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:final-decision-memo
         ====================================================================-->
    <!-- 査定メモ -->
    <xsl:template match="jp:final-decision-memo">
        <xsl:apply-templates select="jp:document-name" />
        <xsl:apply-templates select="jp:final-decision-bibliog" />
        <xsl:apply-templates select="jp:final-decision-body" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:application-reference
         ====================================================================-->
    <!-- 出願書類参照  -->
    <xsl:template match="jp:application-reference">
        <xsl:if test="ancestor::jp:parent-application-article">
            <xsl:if test="position() = 1">
                <xsl:element name="div">
                    <xsl:value-of select="'　対応する原出願の出願番号、原出願の出願日'" />
                </xsl:element>
            </xsl:if>
        </xsl:if>
        <xsl:apply-templates select="jp:document-id" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:drafting-date
         ====================================================================-->
    <!-- 起案日  -->
    <xsl:template match="jp:drafting-date">
        <xsl:apply-templates select="jp:date" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:draft-person-group
         ====================================================================-->
    <!-- 起案者  -->
    <xsl:template match="jp:draft-person-group">
        <xsl:choose>
            <xsl:when
                test="$node = 'jp:examiner-notification-a2515'
                    or $node = 'jp:examiner-notification-a2516'
                    or $node = 'jp:examiner-notification-a2522'">
                <xsl:value-of select="'　特許庁長官　　　　　　　　'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a30'">
                <xsl:value-of select="'　作成者　　　　　　　　　　'" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="'　特許庁審査官　　　　　　　'" />
            </xsl:otherwise>
        </xsl:choose>
        
        <xsl:apply-templates select="jp:name" />
        <xsl:value-of select="'　　'"/>
        <xsl:apply-templates select="jp:staff-code" />
        <xsl:value-of select="'　'"/>
        <xsl:apply-templates select="jp:office-code" />
    </xsl:template>
    
    <!-- ====================================================================
         invention-title
         ====================================================================-->
    <!-- 発明または考案の名称  -->
    <xsl:template match="invention-title">
        <xsl:choose>
            <xsl:when test="$kind-of-law = 'patent'">
                <xsl:value-of select="'　発明の名称　　　　　　　　'" />
            </xsl:when>
            <xsl:when test="$kind-of-law = 'utility'">
                <xsl:value-of select="'　考案の名称　　　　　　　　'" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="'　　　　　　　　　　　　　　'" />
            </xsl:otherwise>
        </xsl:choose>
        
        <xsl:apply-templates />
    </xsl:template>
    
    <!-- ====================================================================
         jp:number-of-claim
         ====================================================================-->
    <!-- 請求項の数  -->
    <xsl:template match="jp:number-of-claim">
        <xsl:choose>
            <xsl:when test="./@jp:adopted-law = 'claim'">
                <xsl:value-of select="'　請求項の数　　　　　　　　'" />
            </xsl:when>
            <xsl:when test="./@jp:adopted-law = 'invention'">
                <xsl:value-of select="'　特許請求の範囲に記載された発明の数　　'" />
            </xsl:when>
        </xsl:choose>
        <xsl:value-of select="."/>
    </xsl:template>
    
    <!-- ====================================================================
         jp:addressed-to-person-group
         ====================================================================-->
    <!-- あて先  -->
    <xsl:template match="jp:addressed-to-person-group">
        <xsl:call-template name="あて先取得" />
        <xsl:apply-templates select="jp:addressbook" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:article-group
         ====================================================================-->
    <!-- 適用条文グループ  -->
    <xsl:template match="jp:article-group">
        <xsl:value-of select="'　適用条文　　　　　　　　　'" />
        <xsl:apply-templates select="jp:article" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:remark
         ====================================================================-->
    <!-- 備考 -->
    <xsl:template match="jp:remark">
        <xsl:element name="div">
            <xsl:apply-templates select="p" mode="indentnasi" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         p
         ====================================================================-->
    <!-- 段落、段落内テキスト  -->
    <xsl:template match="p">
        <xsl:element name="div">
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:heading
         ====================================================================-->
    <!-- 中央段落  -->
    <xsl:template match="jp:heading">
        <xsl:element name="div">
            <xsl:attribute name="class" select="'heading-center'"/> 
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:approval-column-article
         ====================================================================-->
    <!-- 決裁欄  -->
    <xsl:template match="jp:approval-column-article">
        <xsl:element name="div">
            <xsl:apply-templates select="jp:staff1-group/jp:official-title" />
            <xsl:apply-templates select="jp:staff2-group/jp:official-title" />
            <xsl:apply-templates select="jp:staff3-group/jp:official-title" />
            <xsl:apply-templates select="jp:staff4-group/jp:official-title" />
            <xsl:choose>
                <xsl:when test="//@jp:grant = 'post'">
                    <xsl:if test="following-sibling::jp:devider">
                        <xsl:apply-templates select="following-sibling::jp:devider/jp:official-title" />
                    </xsl:if>
                </xsl:when>
            </xsl:choose>
        </xsl:element>
        
        <xsl:element name="div">
            <xsl:if test="not(//@jp:grant = 'post')">
                <xsl:value-of select="'　　　　　　　'" />
            </xsl:if>
            <xsl:apply-templates select="jp:staff1-group/jp:name" />
            <xsl:apply-templates select="jp:staff2-group/jp:name" />
            <xsl:apply-templates select="jp:staff3-group/jp:name" />
            <xsl:apply-templates select="jp:staff4-group/jp:name" />
            <xsl:choose>
                <xsl:when test="//@jp:grant = 'post'">
                    <xsl:if test="following-sibling::jp:devider">
                        <xsl:apply-templates select="following-sibling::jp:devider/jp:name" />
                    </xsl:if>
                </xsl:when>
            </xsl:choose>
            
        </xsl:element>
        
        <xsl:element name="div">
            <xsl:if test="not(//@jp:grant = 'post')">
                <xsl:value-of select="'　　　　　　　'" />
            </xsl:if>
            <xsl:apply-templates select="jp:staff1-group/jp:staff-code" />
            <xsl:apply-templates select="jp:staff2-group/jp:staff-code" />
            <xsl:apply-templates select="jp:staff3-group/jp:staff-code" />
            <xsl:apply-templates select="jp:staff4-group/jp:staff-code" />
            <U>
                <xsl:value-of select="'　'" />
            </U>
            <xsl:choose>
                <xsl:when test="//@jp:grant = 'post'">
                    <xsl:if test="following-sibling::jp:devider">
                        <xsl:apply-templates select="following-sibling::jp:devider/jp:staff-code" />
                    </xsl:if>
                </xsl:when>
            </xsl:choose>
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:patent-law-section30 特許法第３０条適用有無
         jp:change-flag-invention-title 発明の名称の変更有無
         jp:exist-of-reference-doc 参考文献有無
         ====================================================================-->
    <xsl:template match="jp:exist-of-reference-doc |
        jp:patent-law-section30 | jp:change-flag-invention-title">
        <xsl:variable name="key">
            <xsl:value-of select="name()"/>
            <xsl:choose>
                <xsl:when test="$kind-of-law = 'patent'">
                    <xsl:value-of select="'-p'"/>
                </xsl:when>
                <xsl:when test="$kind-of-law = 'utility'">
                    <xsl:value-of select="'-u'"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="item" select="key('ntc-pt-e-conv1-table', $key, $ntc-pt-e-conv1)[1]" />
        <xsl:element name="div">
            <xsl:value-of select="$item/@jp-tag" />
            <xsl:choose>
                <xsl:when test="./@jp:true-or-false = 'true'">
                    <xsl:value-of select="'有'" />
                </xsl:when>
                <xsl:when test="./@jp:true-or-false = 'false'">
                    <xsl:value-of select="'無'" />
                </xsl:when>
            </xsl:choose>
        </xsl:element>
    </xsl:template>
    <!-- The template above is an alternative to a template of the following pattern. -->
    <!-- <xsl:template match="jp:patent-law-section30-OBSOLETE">
         <xsl:element name="div">
         <xsl:value-of select="'３．特許法第３０条適用　　　'" />
         
         <xsl:choose>
         <xsl:when test="./@jp:true-or-false = 'true'">
         <xsl:value-of select="'有'" />
         </xsl:when>
         <xsl:when test="./@jp:true-or-false = 'false'">
         <xsl:value-of select="'無'" />
         </xsl:when>
         </xsl:choose>
         </xsl:element>
         </xsl:template>
    -->
    
    <xsl:key name="ntc-pt-e-conv1-table" match="item" use="@tag"/>
    <xsl:variable name="ntc-pt-e-conv1">
        <item tag="jp:exist-of-reference-doc-p" jp-tag="２．参考文献　　　　　　　　"/>
        <item tag="jp:patent-law-section30-p" jp-tag="３．特許法第３０条適用　　　" />
        <item tag="jp:change-flag-invention-title-p" jp-tag="４．発明の名称の変更　　　　" />
        <item tag="jp:change-flag-invention-title-u" jp-tag="４．考案の名称の変更　　　　" />
    </xsl:variable>
    
    <!-- ====================================================================
         jp:ipc-article
         ====================================================================-->
    <!-- 国際特許分類の記事  -->
    <xsl:template match="jp:ipc-article">
        <xsl:element name="div">
            <xsl:value-of select="'５．国際特許分類（ＩＰＣ）'" />
        </xsl:element>
        <xsl:for-each select="jp:ipc">
            <xsl:apply-templates select="." />
        </xsl:for-each>
    </xsl:template>
    
    <!-- ====================================================================
         jp:classification-article
         ====================================================================-->
    <!-- 併記特許分類の記事  -->
    <xsl:template match="jp:classification-article">
        <xsl:choose>
            <xsl:when test="number(normalize-space(preceding::jp:drafting-date/jp:date)) &gt;= 20050401"/>
            <xsl:when test="string-length(normalize-space(preceding::jp:drafting-date/jp:date)) = 0"/>
            <xsl:otherwise>
                <xsl:element name="div">
                    <xsl:value-of select="'６．併記特許分類'" />
                </xsl:element>
                <xsl:apply-templates select="jp:version-number" />
                <xsl:for-each select="jp:ipc">
                    <xsl:apply-templates select="." />
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         jp:deposit-article
         ====================================================================-->
    <!-- 菌寄託の記事  -->
    <xsl:template match="jp:deposit-article">
        <xsl:element name="div">
            <xsl:choose>
                <xsl:when test="ancestor::jp:final-decision-group">
                    <xsl:choose>
                        <xsl:when
                            test="number(normalize-space(preceding::jp:drafting-date/jp:date)) &gt;= 20050401">
                            <xsl:value-of select="'６．菌寄託'" />
                        </xsl:when>
                        <xsl:when
                            test="string-length(normalize-space(preceding::jp:drafting-date/jp:date)) = 0">
                            <xsl:value-of select="'６．菌寄託'" />
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'７．菌寄託'" />
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="ancestor::jp:final-decision-memo">
                    <xsl:choose>
                        <xsl:when test="preceding-sibling::jp:exceptions-to-lack-of-novelty-art">
                            <xsl:value-of select="'５．菌寄託'" />
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'４．菌寄託'" />
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
            </xsl:choose>
        </xsl:element>
        
        <xsl:apply-templates select="jp:deposit" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:parent-application-article
         ====================================================================-->
    <!-- 分割変更表示の記事  -->
    <xsl:template match="jp:parent-application-article">
        <xsl:element name="div">
            <xsl:choose>
                <xsl:when
                    test="number(normalize-space(preceding::jp:drafting-date/jp:date)) &gt;= 20050401">
                    <xsl:value-of select="'７．出願日の遡及を認めない旨の表示'" />
                </xsl:when>
                <xsl:when test="string-length(normalize-space(preceding::jp:drafting-date/jp:date)) = 0">
                    <xsl:value-of select="'７．出願日の遡及を認めない旨の表示'" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'８．分割・変更の遡及を認めない旨の表示'" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
        <xsl:apply-templates select="jp:application-reference" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:final-decision-bibliog
         ====================================================================-->
    <!-- メモ内書誌部  -->
    <xsl:template match="jp:final-decision-bibliog">
        <xsl:element name="div">
            <xsl:apply-templates select="jp:application-reference" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:final-decision-body
         ====================================================================-->
    <!-- メモ内本文部  -->
    <xsl:template match="jp:final-decision-body">
        <xsl:apply-templates select="jp:field-of-search-article" />
        <xsl:apply-templates select="jp:patent-reference-article" />
        <xsl:apply-templates select="jp:reference-books-article" />
        <xsl:apply-templates select="jp:exceptions-to-lack-of-novelty-art" />
        <xsl:apply-templates select="jp:deposit-article" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:administrative-appeal-sentence
         ====================================================================-->
    <xsl:template match="jp:administrative-appeal-sentence">
        <!-- 未サポート -->
        <xsl:element name="div">
            <xsl:apply-templates select="p" mode="misapo" />
            <xsl:if test="jp:approval-column-article">
                <xsl:apply-templates
                    select="jp:staff1-group | jp:staff2-group | jp:staff3-group
                        | jp:staff4-group | jp:devider"
                    mode="misapo" />
            </xsl:if>
            <xsl:apply-templates select="jp:approval-without-contents" mode="misapo" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:document-id
         ====================================================================-->
    <!-- ドキュメント識別 -->
    <xsl:template match="jp:document-id">
        <xsl:apply-templates select="jp:doc-number | jp:date" />
        
        <xsl:if test="country or kind or name">
            <xsl:apply-templates select="country | kind | name" mode="misapo" />
        </xsl:if>
    </xsl:template>
    
    <!-- ====================================================================
         jp:date 日付; call-template name="日付変換" 
         ====================================================================-->
    <xsl:template match="jp:date">
        <xsl:call-template name="日付タイトル" />
        <xsl:call-template name="call-template-if-no-error"/>
    </xsl:template>
    
    <!-- ====================================================================
         jp:name 氏名、氏名または名称; call-template name="氏名編集"
         jp:doc-number 文書番号; call-template name="文書番号編集"
         ====================================================================-->
    <xsl:template match="jp:name | jp:doc-number">
        <xsl:call-template name="call-template-if-no-error"/>
    </xsl:template>
    
    <!-- ====================================================================
         jp:name
         ====================================================================-->
    <!-- 氏名、氏名または名称 -->
    <xsl:template name="call-template-if-no-error">
        <xsl:choose>
            <xsl:when test="./@jp:error-code">
                <xsl:value-of select="." />
            </xsl:when>
            <xsl:when test="name() = 'jp:date'">
                <xsl:call-template name="日付変換" />
            </xsl:when>
            <xsl:when test="name() = 'jp:name'">
                <xsl:call-template name="氏名編集" />
            </xsl:when>
            <xsl:when test="name() = 'jp:doc-number'">
                <xsl:call-template name="文書番号編集" />
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         jp:staff-code 半角全角変換は省略、前後空白埋め省略
         ====================================================================-->
    <!-- 担当者コード -->
    <xsl:template match="jp:staff-code">
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>
    
    <!-- ====================================================================
         jp:office-code 半角全角変換は省略
         jp:official-title 先頭の空白埋めは省略
         ====================================================================-->
    <!-- 所属コード -->
    <xsl:template match="jp:office-code | jp:official-title">
        <xsl:value-of select="."/>
    </xsl:template>
    
    <!-- ====================================================================
         jp:article
         ====================================================================-->
    <!-- 適用条文 -->
    <xsl:template match="jp:article">
        <xsl:if test="position() != 1">
            <xsl:value-of select="'、'" />
        </xsl:if>
        <xsl:value-of select="." />
    </xsl:template>
    
    <!-- ====================================================================
         jp:ipc 半角全角変換は省略
         ====================================================================-->
    <xsl:template match="jp:ipc">
        <xsl:element name="div">
            <xsl:value-of select="'　　　　　　　　　　　　　　' || ." />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:version-number 半角全角変換は省略
         ====================================================================-->
    <!-- 版コード -->
    <xsl:template match="jp:version-number">
        <xsl:element name="div">
            <xsl:value-of select="'　版コード　　　' || ." />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:deposit 半角全角変換は省略
         ====================================================================-->
    <!-- 菌寄託 -->
    <xsl:template match="jp:deposit">
        <xsl:element name="div">
            <xsl:value-of select="'　菌寄託' || ./@jp:serial-number" />
        </xsl:element>
        
        <xsl:apply-templates select="jp:depository-ins-code" />
        <xsl:apply-templates select="jp:depository-number" />
    </xsl:template>
    
    <!-- ====================================================================
         jp:field-of-search-article
         ====================================================================-->
    <!-- 調査分野の記事 -->
    <xsl:template match="jp:field-of-search-article">
        <xsl:element name="div">
            <xsl:choose>
                <xsl:when test="number(normalize-space(//jp:drafting-date/jp:date)) &gt; 20060100">
                    <xsl:value-of select="'１．調査した分野（ＩＰＣ，ＤＢ名）'" />
                </xsl:when>
                <xsl:when test="string-length(normalize-space(preceding::jp:drafting-date/jp:date)) = 0">
                    <xsl:value-of select="'１．調査した分野（ＩＰＣ，ＤＢ名）'" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'１．調査した分野（ＩＰＣ第７版，ＤＢ名）'" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element> 
        
        <xsl:for-each select="jp:field-of-search">
            <xsl:element name="div">
                <xsl:apply-templates select="." />
            </xsl:element>
        </xsl:for-each>
    </xsl:template>
    
    <!-- ====================================================================
         jp:patent-reference-article
         ====================================================================-->
    <!-- 参考特許文献の記事 -->
    <xsl:template match="jp:patent-reference-article">
        <xsl:element name="div">
            <xsl:value-of select="'２．参考特許文献'" />
        </xsl:element>
        
        <xsl:for-each select="jp:patent-reference-group">
            <xsl:apply-templates select="." />
        </xsl:for-each>
    </xsl:template>
    
    <!-- ====================================================================
         jp:reference-books-article
         ====================================================================-->
    <!-- 参考図書雑誌の記事 -->
    <xsl:template match="jp:reference-books-article">
        <xsl:element name="div">
            <xsl:value-of select="'３．参考図書雑誌'" />
        </xsl:element>
        <xsl:for-each select="jp:reference-books">
            <xsl:element name="div">
                <xsl:apply-templates select="." />
            </xsl:element>
        </xsl:for-each>
    </xsl:template>
    
    <!-- ====================================================================
         jp:exceptions-to-lack-of-novelty-art
         ====================================================================-->
    <!-- 新規性喪失例外の記事 -->
    <xsl:template match="jp:exceptions-to-lack-of-novelty-art">
        <xsl:element name="div">
            <xsl:value-of select="'４．新規性喪失例外規定の適用の事実'" />
        </xsl:element>
        <xsl:for-each select="jp:exceptions-to-lack-of-novelty-grp">
            <xsl:apply-templates select="." />
        </xsl:for-each>
    </xsl:template>
    
    <!-- ====================================================================
         jp:depository-ins-code 半角全角変換は省略、先頭空白うめ省略
         ====================================================================-->
    <!-- 受託機関コード -->
    <xsl:template match="jp:depository-ins-code">
        <xsl:element name="div">
            <xsl:value-of select="'　　受託機関コード' || ." />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:depository-number 半角全角変換は省略、先頭空白うめ省略
         ====================================================================-->
    <!-- 受託番号 -->
    <xsl:template match="jp:depository-number">
        <xsl:element name="div">
            <xsl:value-of select="'　　受託番号' || ." />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:field-of-search
         ====================================================================-->
    <!-- 調査分野 -->
    <xsl:template match="jp:field-of-search">
        <xsl:value-of select="'　' || ." />
    </xsl:template>
    
    <!-- ====================================================================
         jp:patent-reference-group
         ====================================================================-->
    <!-- 参考特許文献グル－プ -->
    <xsl:template match="jp:patent-reference-group">
        <xsl:element name="div">
            <xsl:element name="span">
                <xsl:value-of select="./jp:document-number" />
            </xsl:element>
            <xsl:element name="span">
                <xsl:value-of select="./jp:kind-of-document" />
            </xsl:element>
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:reference-books
         ====================================================================-->
    <!-- 参考図書雑誌 -->
    <xsl:template match="jp:reference-books">
        <xsl:value-of select="'　' || ." />
    </xsl:template>
    
    <!-- ====================================================================
         jp:exceptions-to-lack-of-novelty-grp
         ====================================================================-->
    <!-- 新規性喪失の例外 -->
    <xsl:template match="jp:exceptions-to-lack-of-novelty-grp">
        <xsl:element name="div">
            <xsl:value-of select="'　新規性喪失の例外' || ./@jp:serial-number" />
        </xsl:element>
        <xsl:element name="div">
            <xsl:apply-templates select="jp:application-section" />
        </xsl:element>
        <xsl:element name="div">
            <xsl:apply-templates select="jp:exceptions-to-lack-of-novelty" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         jp:addressbook
         ====================================================================-->
    <xsl:template match="jp:addressbook">
    </xsl:template>
    
    <!-- ====================================================================
         br
         ====================================================================-->
    <!-- 段落内改行 -->
    <xsl:template match="br">
        <br />
    </xsl:template> 
    
    <!-- ====================================================================
         u
         ====================================================================-->
    <!-- 下線 -->
    <xsl:template match="u">
        <u>
            <xsl:apply-templates />
        </u>
    </xsl:template>
    
    <!-- ====================================================================
         sup
         ====================================================================-->
    <!-- 上付  -->
    <xsl:template match="sup">
        <sup>
            <xsl:apply-templates />
        </sup>
    </xsl:template>
    
    <!-- ====================================================================
         sub
         ====================================================================-->
    <!-- 下付 -->
    <xsl:template match="sub">
        <sub>
            <xsl:apply-templates />
        </sub>
    </xsl:template>
    
    <!-- ====================================================================
         img
         ====================================================================-->
    <!-- イメージ  -->
    <xsl:template match="img">
        <xsl:variable name="item" select="key('image-table', @file)[1]" />
        
        <xsl:element name="div">
            <xsl:element name="img">
                <xsl:attribute name="src">
                    <xsl:value-of select="$item/@new" />
                </xsl:attribute>
                <xsl:attribute name="width">
                    <xsl:value-of select="$item/@width" />
                </xsl:attribute>
                <xsl:attribute name="height">
                    <xsl:value-of select="$item/@height" />
                </xsl:attribute>
            </xsl:element>
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         ul
         ====================================================================-->
    <!-- インデント付段落 -->
    <xsl:template match="p/ul">
        <xsl:apply-templates />
    </xsl:template>
    
    <!-- ====================================================================
         li
         ====================================================================-->
    <!-- インデント付段落 -->
    <xsl:template match="li">
        <xsl:choose>
            <xsl:when test="./ul">
                <xsl:apply-templates />
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="count(ancestor::ul) = 1">
                        <xsl:element name="div">
                            <xsl:value-of select="'　'" />
                            <xsl:apply-templates />
                        </xsl:element>
                    </xsl:when>
                    <xsl:when test="count(ancestor::ul) = 2">
                        <xsl:element name="div">
                            <xsl:value-of select="'　　'" />
                            <xsl:apply-templates />
                        </xsl:element>
                    </xsl:when>
                    <xsl:when test="count(ancestor::ul) = 3">
                        <xsl:element name="div">
                            <xsl:value-of select="'　　　'" />
                            <xsl:apply-templates />
                        </xsl:element>
                    </xsl:when>
                    <xsl:when test="count(ancestor::ul) = 4">
                        <xsl:element name="div">
                            <xsl:value-of select="'　　　　'" />
                            <xsl:apply-templates />
                        </xsl:element>
                    </xsl:when>
                    <xsl:when test="count(ancestor::ul) = 5">
                        <xsl:element name="div">
                            <xsl:value-of select="'　　　　　'" />
                            <xsl:apply-templates />
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="div">
                            <xsl:value-of select="'　　　　　　'" />
                            <xsl:apply-templates />
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
        
        <xsl:choose>
            <xsl:when test="./ul">
            </xsl:when>
            <xsl:otherwise>
                <BR />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    
    <!-- ====================================================================
         jp:application-section
         ====================================================================-->
    <!-- 適用条項 -->
    <xsl:template match="jp:application-section">
        <xsl:value-of select="'　　適用条文　　　　'" />
        
        <xsl:choose>
            <xsl:when test="$kind-of-law = 'patent'">
                <xsl:value-of select="'特許法第３０条' || . || 'の規定の適用'" />
            </xsl:when>
            <xsl:when test="$kind-of-law = 'utility'">
                <xsl:value-of select="'実用新案法第９条第１項で準用する特許法第３０条' || . || 'の規定の適用'" />
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         jp:exceptions-to-lack-of-novelty
         ====================================================================-->
    <!-- 新規性喪失例外適用 -->
    <xsl:template match="jp:exceptions-to-lack-of-novelty">
        <xsl:value-of select="'　　内容　　　　　　'" />
        <xsl:apply-templates select="p" mode="indentnasi" />
    </xsl:template>
    
    <!-- ====================================================================
         p　（インデント編集なし）
         ====================================================================-->
    <!-- 段落、段落内テキスト （インデント編集なし） -->
    <xsl:template match="p" mode="indentnasi">
        <xsl:choose>
            <xsl:when test="parent::jp:remark">
                <xsl:value-of select="'　備考　　　　　　　　　　　'" />
            </xsl:when>
        </xsl:choose>
        <xsl:apply-templates />
    </xsl:template>
    
    <!-- ====================================================================
         タイトル編集
         ====================================================================-->
    <xsl:template name="タイトル編集">
        <xsl:choose>
            <xsl:when
                test="($node = 'jp:decision-of-registration-a01') and ($kind-of-law = 'patent')">
                <xsl:value-of select="'特許査定'" />
            </xsl:when>
            <xsl:when
                test="($node = 'jp:decision-of-registration-a01') and ($kind-of-law = 'utility')">
                <xsl:value-of select="'登録査定'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:decision-of-rejection-a02'">
                <xsl:value-of select="'拒絶査定'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:notice-of-rejection-a131'">
                <xsl:value-of select="'拒絶理由通知書'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:declining-the-amendment-a191'">
                <xsl:value-of select="'補正の却下の決定'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:declining-the-amendment-a192'">
                <xsl:value-of select="'補正の却下の決定'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a251'">
                <xsl:value-of select="'審査官通知（その他の通知）（期間有）'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a2514'">
                <xsl:value-of select="'立会実験申請書の提出命令書'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a2515'">
                <xsl:value-of select="'同一出願人による同日出願通知書'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a2516'">
                <xsl:value-of select="'出願人相違の同日出願通知書'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a252'">
                <xsl:value-of select="'審査官通知（その他の通知）（期間無）'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a2522'">
                <xsl:value-of select="'先願未請求による審査不可能通知書'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a2529'">
                <xsl:value-of select="'先行技術文献情報不開示の通知'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a25110'">
                <xsl:value-of select="'１９４条の通知（分割出願に関する説明書）'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a25111'">
                <xsl:value-of select="'１９４条の通知（その他）'" />
            </xsl:when>
            <xsl:when test="$node = 'jp:examiner-notification-a30'">
                <xsl:value-of select="'引用非特許文献'" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="." />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         文書番号編集
         ====================================================================-->
    <xsl:template name="文書番号編集">
        <xsl:variable name="kind-of-law" select="ancestor::jp:application-reference/@jp:kind-of-law" />
        
        <xsl:choose>
            <xsl:when
                test="ancestor::jp:parent-application-article
                    and ancestor::jp:parent-application-article [@jp:kind-of-application = 'division']">
                <xsl:value-of select="'　分割出願　　　　　　　　　'" />
            </xsl:when>
            <xsl:when
                test="ancestor::jp:parent-application-article
                    and ancestor::jp:parent-application-article [@jp:kind-of-application = 'change']">
                <xsl:value-of select="'　変更出願　　　　　　　　　'" />
            </xsl:when>
            <xsl:when
                test="ancestor::jp:parent-application-article
                    and ancestor::jp:parent-application-article [@jp:kind-of-application = 'based-on-utility']">
                <xsl:value-of select="'　実用基礎　　　　　　　　　'" />
            </xsl:when>
            <xsl:when
                test="ancestor::jp:application-reference
                    and $kind-of-law = 'patent'">
                <xsl:value-of select="'　特許出願の番号　　　　　　'" />
            </xsl:when>
            <xsl:when
                test="ancestor::jp:application-reference
                    and $kind-of-law = 'utility'">
                <xsl:value-of select="'　実用新案登録出願の番号　　'" />
            </xsl:when>
        </xsl:choose>
        
        <xsl:choose>
            <xsl:when test="number(normalize-space(.)) &gt;= 2000000000">
                <xsl:choose>
                    <xsl:when test="$kind-of-law = 'patent'">
                        <xsl:value-of select="'特願'" />
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'utility'">
                        <xsl:value-of select="'実願'" />
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'design'">
                        <xsl:value-of select="'意願'" />
                    </xsl:when>
                </xsl:choose>
                <xsl:value-of
                    select="substring(normalize-space(.),1,4) || '－' ||
                        substring(normalize-space(.),5,6)" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="和暦変換" />
                <xsl:choose>
                    <xsl:when test="$kind-of-law = 'patent'">
                        <xsl:value-of select="'　特許願　'" />
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'utility'">
                        <xsl:value-of select="'　実用新案登録願　'" />
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'design'">
                        <xsl:value-of select="'　意匠登録願　'" />
                    </xsl:when>
                </xsl:choose>
                <xsl:value-of
                    select="'第' || substring(normalize-space(.),5,6) || '号'" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         和暦変換
         ====================================================================-->
    <xsl:template name="和暦変換">
        <xsl:variable name="day" select="normalize-space(.)" />
        
        <xsl:choose>
            <xsl:when test="(number($day) &gt;= 1912000001) and (number($day) &lt;= 1926000000)">
                <xsl:call-template name="大正編集" />
            </xsl:when>
            <xsl:when test="(number($day) &gt;= 1868000001) and (number($day) &lt;= 1912000000)">
                <xsl:call-template name="明治編集" />
            </xsl:when>
            <xsl:when test="number($day) &lt;= 1868000000">
                <xsl:value-of select="'不明'" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="ancestor::jp:application-reference [@jp:kind-of-law = 'patent']">
                        <xsl:choose>
                            <xsl:when test="number($day) &gt;= 1989001147">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when
                        test="ancestor::jp:application-reference [@jp:kind-of-law = 'utility']">
                        <xsl:choose>
                            <xsl:when test="number($day) &gt;= 1989000492">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="ancestor::jp:application-reference [@jp:kind-of-law = 'design']">
                        <xsl:choose>
                            <xsl:when test="number($day) &gt;= 1989000125">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         日付タイトル
         ====================================================================-->
    <xsl:template name="日付タイトル">
        <xsl:choose>
            <xsl:when test="ancestor::jp:drafting-date">
                <xsl:choose>
                    <xsl:when test="$node = 'jp:examiner-notification-a30'">
                        <xsl:value-of select="'　作成日　　　　　　　　　　'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'　起案日　　　　　　　　　　'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="'　　　　　　　　　　　　　　'" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         日付変換
         ====================================================================-->
    <xsl:template name="日付変換">
        <xsl:variable name="m" select="substring(normalize-space(.),5,2)" />
        <xsl:variable name="d" select="substring(normalize-space(.),7,2)" />
        
        <xsl:call-template name="gengo">
            <xsl:with-param name="date" select="normalize-space(.)" />
        </xsl:call-template>
        <xsl:call-template name="warekinen">
            <xsl:with-param name="date" select="normalize-space(.)" />
        </xsl:call-template>
        <xsl:value-of select="'年'" />
        <xsl:value-of select="$m || '月'" />
        <xsl:value-of select="$d || '日'" />
    </xsl:template>
    
    <!-- ====================================================================
         氏名編集 空白埋め省略
         ====================================================================-->
    <xsl:template name="氏名編集">
        <xsl:choose>
            <xsl:when
                test="($node = 'jp:examiner-notification-a2515'
                        or $node = 'jp:examiner-notification-a2516'
                        or $node = 'jp:examiner-notification-a2522')
                    and ancestor::jp:draft-person-group">
                <xsl:value-of select="'　　　　　　　　　　　　　'" />
            </xsl:when>
            <xsl:when
                test="($node != 'jp:examiner-notification-a2515'
                        and $node != 'jp:examiner-notification-a2516'
                        and $node != 'jp:examiner-notification-a2522')
                    and ancestor::jp:draft-person-group">
                <xsl:value-of select="normalize-space(.)" />
            </xsl:when>
            <xsl:when test="ancestor::jp:addressed-to-person-group">
                <xsl:value-of select="normalize-space(.)" />
            </xsl:when>
            <xsl:when
                test="ancestor::jp:staff1-group or ancestor::jp:staff2-group
                    or ancestor::jp:staff3-group or ancestor::jp:staff4-group
                    or ancestor::jp:devider">
                <u>
                    <xsl:value-of select="normalize-space(.)" />
                </u>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
    </xsl:template>
    
    <!-- ====================================================================
         あて先取得
         ====================================================================-->
    <xsl:template name="あて先取得">
        <xsl:variable name="name" select="normalize-space(.//jp:name)" />
        <xsl:choose>
            <xsl:when test="./@jp:kind-of-person = 'applicant'">
                <xsl:choose>
                    <xsl:when test="$kind-of-law = 'utility'">
                        <xsl:choose>
                            <xsl:when test="./@jp:kind-of-representative = 'representative-application'">
                                <xsl:choose>
                                    <xsl:when test="./@jp:kind-of-agent = 'representative'">
                                        <xsl:value-of select="'　実用新案登録代表出願人代理人　'" />
                                    </xsl:when>
                                    <xsl:when test="./@jp:kind-of-agent = 'sub-representative'">
                                        <xsl:value-of select="'　実用新案登録代表出願人復代理人　'" />
                                    </xsl:when>
                                    <xsl:when test="./@jp:kind-of-agent = 'legal-representative'">
                                        <xsl:value-of select="'　実用新案登録代表出願人法定代理人　'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="./@jp:kind-of-agent = 'designated-representative'">
                                        <xsl:value-of select="'　実用新案登録代表出願人指定代理人　'" />
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="'　実用新案登録代表出願人　　'" />
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:choose>
                                    <xsl:when test="./@jp:kind-of-agent = 'representative'">
                                        <xsl:value-of select="'　実用新案登録出願人代理人　'" />
                                    </xsl:when>
                                    <xsl:when test="./@jp:kind-of-agent = 'sub-representative'">
                                        <xsl:value-of select="'　実用新案登録出願人復代理人　'" />
                                    </xsl:when>
                                    <xsl:when test="./@jp:kind-of-agent = 'legal-representative'">
                                        <xsl:value-of select="'　実用新案登録出願人法定代理人　'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="./@jp:kind-of-agent = 'designated-representative'">
                                        <xsl:value-of select="'　実用新案登録出願人指定代理人　'" />
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="'　実用新案登録出願人　　　　'" />
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'patent'">
                        <xsl:choose>
                            <xsl:when
                                test="./@jp:kind-of-representative = 'representative-application'">
                                <xsl:choose>
                                    <xsl:when test="./@jp:kind-of-agent = 'representative'">
                                        <xsl:value-of select="'　特許代表出願人代理人　　　'" />
                                    </xsl:when>
                                    <xsl:when test="./@jp:kind-of-agent = 'sub-representative'">
                                        <xsl:value-of select="'　特許代表出願人復代理人　　'" />
                                    </xsl:when>
                                    <xsl:when test="./@jp:kind-of-agent = 'legal-representative'">
                                        <xsl:value-of select="'　特許代表出願人法定代理人　'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="./@jp:kind-of-agent = 'designated-representative'">
                                        <xsl:value-of select="'　特許代表出願人指定代理人　'" />
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="'　特許代表出願人　　　　　　'" />
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:choose>
                                    <xsl:when test="./@jp:kind-of-agent = 'representative'">
                                        <xsl:value-of select="'　特許出願人代理人　　　　　'" />
                                    </xsl:when>
                                    <xsl:when test="./@jp:kind-of-agent = 'sub-representative'">
                                        <xsl:value-of select="'　特許出願人復代理人　　　　'" />
                                    </xsl:when>
                                    <xsl:when test="./@jp:kind-of-agent = 'legal-representative'">
                                        <xsl:value-of select="'　特許出願人法定代理人　　　'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="./@jp:kind-of-agent = 'designated-representative'">
                                        <xsl:value-of select="'　特許出願人指定代理人　　　'" />
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="'　特許出願人　　　　　　　　'" />
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="./@jp:kind-of-person = 'attorney'">
                <xsl:choose>
                    <xsl:when test="./@jp:kind-of-agent = 'representative'">
                        <xsl:value-of select="'　代理人　　　　　　　　　　'" />
                    </xsl:when>
                    <xsl:when test="./@jp:kind-of-agent = 'sub-representative'">
                        <xsl:value-of select="'　復代理人　　　　　　　　　'" />
                    </xsl:when>
                    <xsl:when test="./@jp:kind-of-agent = 'legal-representative'">
                        <xsl:value-of select="'　法定代理人　　　　　　　　'" />
                    </xsl:when>
                    <xsl:when test="./@jp:kind-of-agent = 'designated-representative'">
                        <xsl:value-of select="'　指定代理人　　　　　　　　'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'　　　　　　　　　　　　　　'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
        
        <xsl:variable name="persons" select="normalize-space(.//jp:number-of-other-persons)" />
        
        <xsl:value-of select="$name" />
        <xsl:if test=".//jp:number-of-other-persons">
            <xsl:value-of select="'（外' || $persons || '名）'" />
        </xsl:if>
        <xsl:if
            test="$node = 'jp:notice-of-rejection-a131' or $node = 'jp:examiner-notification-a2514'
                or $node = 'jp:examiner-notification-a2515' or $node = 'jp:examiner-notification-a2516'
                or $node = 'jp:examiner-notification-a251' or $node = 'jp:examiner-notification-a2522'
                or $node = 'jp:examiner-notification-a252' or $node = 'jp:examiner-notification-a2529'
                or $node = 'jp:examiner-notification-a25110' or $node = 'jp:examiner-notification-a25111'">
            <xsl:value-of select="'　様'" />
        </xsl:if>
        
    </xsl:template>
    
    <!-- ====================================================================
         未サポートタグ（全角空白１つあけて表示）
         ====================================================================-->
    <xsl:template
        match="jp:kana | country | kind | name | last-name
            | first-name | midle-name | iid | role | orgname | orgname | department
            | synonym | jp:phone | jp:fax | email | url | ead | dtext | text
            | jp:approval-without-contents | jp:file-reference-id"
        mode="misapo">
        
        <xsl:call-template name="タグ編集"/>
    </xsl:template>
    
    <!-- ====================================================================
         未サポートタグ（全角空白２つあけて表示）
         ====================================================================-->
    <xsl:template
        match="jp:addressbook//address-1 | jp:addressbook//address-2 | jp:addressbook//address-3
            | jp:addressbook//address-4 | jp:addressbook//address-5
            | jp:addressbook//mailcode | jp:addressbook//pobox | jp:addressbook//room
            | jp:addressbook//address-floor | jp:addressbook//building | jp:addressbook//street
            | jp:addressbook//city | jp:addressbook//county | jp:addressbook//state
            | jp:addressbook//postcode | jp:addressbook//country | jp:addressbook//jp:text
            | jp:addressbook//jp:original-language-of-address
            | jp:administrative-appeal-sentence/p
            | jp:administrative-appeal-sentence/jp:approval-without-contents
            | jp:administrative-appeal-sentence//jp:certification-column-group"
        mode="misapo">
        
        <xsl:call-template name="タグ編集"/>
    </xsl:template>
    
    <!-- ====================================================================
         未サポートタグ（全角空白３つあけて表示）
         ====================================================================-->
    <xsl:template
        match="jp:administrative-appeal-sentence//jp:staff1-group
            | jp:administrative-appeal-sentence//jp:staff2-group
            | jp:administrative-appeal-sentence//jp:staff3-group
            | jp:administrative-appeal-sentence//jp:staff4-group
            | jp:administrative-appeal-sentence//jp:devider
            | jp:administrative-appeal-sentence//jp:phone
            | jp:administrative-appeal-sentence//jp:fax"
        mode="misapo">
        <xsl:call-template name="タグ編集"/>
    </xsl:template>
    
    <!-- ====================================================================
         未サポートタグ（ｐタグ用）
         ====================================================================-->
    <xsl:template
        match="b | i |smallcaps | ol | figref | patcit | nplcit
            | bio-deposit | crossref | maths | tables | chemistry
            | o | pre | table-external-doc">
        <xsl:element name="div">
            <xsl:value-of select="'&lt;' || name()" />
            <xsl:apply-templates select="./@*" mode="misapo" />
            <xsl:value-of select="'&gt;' || . || '&lt;/' || name() || '&gt;'" />
        </xsl:element>
    </xsl:template>
    
    <!-- ====================================================================
         属性値出力
         ====================================================================-->
    <xsl:template match="@*" mode="misapo">
        <xsl:value-of select="' ' || name() || '=&quot;' || . || '&quot;'" />
    </xsl:template>
    
</xsl:stylesheet>