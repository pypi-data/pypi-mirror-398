<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <!-- this xslt was created with reference to pat_common.xsl
     of Internet Application Software version i5.30 provided by JPO -->

    <xsl:variable name="node" select="name(//jp:pat-app-doc/*)" />
    <xsl:variable name="kind-of-law" select="//jp:pat-app-doc/*/@jp:kind-of-law" />
    <xsl:variable name="kinddoc" select="name(//jp:pat-app-doc/*)" />

    <xsl:include href="sub-templates/pat_appd.xsl" />
    <xsl:include href="common-templates/date-templates.xsl" />
    <xsl:include href="common-templates/string-utils.xsl" />
    <xsl:include href="common-templates/document-code.xsl" />
    <xsl:include href="common-templates/special-mention-matter-article.xsl" />
    <xsl:include href="common-templates/country.xsl" />
    <xsl:include href="common-templates/doc-number.xsl" />

    <xsl:template match="/">
        <xsl:element name="root">
            <xsl:apply-templates select="root/jp:pat-app-doc" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
     jp:application-a63
     ====================================================================-->
    <xsl:template match="jp:application-a63">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:special-mention-matter-article" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:parent-application-article" />
        <xsl:apply-templates select="jp:ipc-article" />
        <xsl:apply-templates select="jp:inventors" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:trust-relation" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:attorney-change-article" />
        <xsl:apply-templates select="jp:priority-claims" />
        <xsl:apply-templates select="jp:declaration-priority-ear-app" />
        <xsl:apply-templates select="jp:law-of-industrial-regenerate" />
        <xsl:apply-templates select="jp:payment-years" />
        <xsl:apply-templates select="jp:share-rate" />
        <xsl:apply-templates select="jp:charge-article" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:proof-necessity" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a631
     ====================================================================-->
    <xsl:template match="jp:application-a631">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:proof-necessity" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:dispatch-number" />
        <xsl:apply-templates select="jp:dispatch-date" />
        <xsl:apply-templates select="jp:notice-contents-group" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a632
     ====================================================================-->
    <xsl:template match="jp:application-a632">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:inventors" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:trust-relation" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:attorney-change-article" />
        <xsl:apply-templates select="jp:law-of-industrial-regenerate" />
        <xsl:apply-templates select="jp:payment-years" />
        <xsl:apply-templates select="jp:share-rate" />
        <xsl:apply-templates select="jp:charge-article" />
        <xsl:apply-templates select="jp:dispatch-number" />
        <xsl:apply-templates select="jp:notice-contents-group" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a633
     ====================================================================-->
    <xsl:template match="jp:application-a633">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:dispatch-number" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a634
     ====================================================================-->
    <xsl:template match="jp:application-a634">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:application-a635
     ====================================================================-->
    <xsl:template match="jp:application-a635">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:notice-contents-group" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

</xsl:stylesheet>