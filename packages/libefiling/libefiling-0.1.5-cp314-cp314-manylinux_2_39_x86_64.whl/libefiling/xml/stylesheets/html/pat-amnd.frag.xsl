<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <xsl:output name="html_out" method="html" encoding="utf-8" omit-xml-declaration="yes"
        doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
        doctype-system="http://www.w3.org/TR/html4/loose.dtd" indent="yes" media-type="text/html" />

    <xsl:variable name="node" select="name(//jp:pat-amnd/*)" />
    <xsl:variable name="kind-of-law" select="//jp:pat-app-doc/*/@jp:kind-of-law" />

    <xsl:include href="parts/pat_common.xsl" />

    <!-- lookup table defined in source xml. -->
    <xsl:key name="procedure-params" match="procedure-param" use="@name" />

    <xsl:template match="/root">
        <xsl:element name="div">
            <xsl:apply-templates select="jp:pat-amnd" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
     jp:amendment-a51 | jp:amendment-a523
     ====================================================================-->
    <xsl:template match="jp:amendment-a51 | jp:amendment-a523">
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
        <xsl:apply-templates select="jp:num-claim-decrease-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:num-claim-increase-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:amendment-article" />
        <xsl:apply-templates select="jp:amendment-charge-article" />
        <xsl:apply-templates select="jp:proof-means" />
        <xsl:apply-templates select="jp:share-rate" />
        <xsl:apply-templates select="jp:charge-article" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:amendment-a524
     ====================================================================-->
    <xsl:template match="jp:amendment-a524">
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
        <xsl:apply-templates select="jp:num-claim-decrease-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:num-claim-increase-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:amendment-article" />
        <xsl:apply-templates select="jp:opinion-contents-article">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:share-rate" />
        <xsl:apply-templates select="jp:charge-article" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:amendment-a525 | jp:amendment-a529
     ====================================================================-->
    <xsl:template match="jp:amendment-a525 | jp:amendment-a529">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:proof-necessity" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:submit-date-of-amendment" />
        <xsl:apply-templates select="jp:num-claim-decrease-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:num-claim-increase-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:amendment-article" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:amendment-a526 | jp:amendment-a5210
     ====================================================================-->
    <xsl:template match="jp:amendment-a526 | jp:amendment-a5210">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:proof-necessity" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:submit-date-of-amendment" />
        <xsl:apply-templates select="jp:num-claim-decrease-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:num-claim-increase-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:notice-contents-group" />
        <xsl:apply-templates select="jp:amendment-article" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:amendment-a527 | jp:amendment-a5211
     ====================================================================-->
    <xsl:template match="jp:amendment-a527 | jp:amendment-a5211">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:proof-necessity" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:submit-date-of-amendment" />
        <xsl:apply-templates select="jp:num-claim-decrease-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:num-claim-increase-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>

    <!-- ====================================================================
     jp:amendment-a528 | jp:amendment-a5212
     ====================================================================-->
    <xsl:template match="jp:amendment-a528 | jp:amendment-a5212">
        <xsl:apply-templates select="jp:document-code" />
        <xsl:apply-templates select="jp:file-reference-id" />
        <xsl:apply-templates select="jp:submission-date" />
        <xsl:apply-templates select="jp:addressed-to-person" />
        <xsl:apply-templates select="jp:indication-of-case-article" />
        <xsl:apply-templates select="jp:proof-necessity" />
        <xsl:apply-templates select="jp:applicants" />
        <xsl:apply-templates select="jp:agents" />
        <xsl:apply-templates select="jp:submit-date-of-amendment" />
        <xsl:apply-templates select="jp:num-claim-decrease-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:num-claim-increase-amendment">
            <xsl:with-param name="document" select="$node" />
        </xsl:apply-templates>
        <xsl:apply-templates select="jp:notice-contents-group" />
        <xsl:apply-templates select="jp:dtext" />
        <xsl:apply-templates select="jp:submission-object-list-article" />
        <xsl:apply-templates select="jp:rule-outside-item-article" />
    </xsl:template>
</xsl:stylesheet>