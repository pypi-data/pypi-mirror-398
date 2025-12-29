# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.2] - 2025-10-29

### Fixed
- Integer field validation by letting ModelForm auto-generate form fields
- Wavelength filtering by value (decimal support)

### Added
- CASCADE deletion tests for grid types and grids
- PROTECT behavior tests for wavelengths in use

## [0.4.0] - 2025-10-17

### Changed
- **BREAKING**: Migrated to NetBox 3.7.8 compatibility
- **BREAKING**: Dropped support for NetBox 2.x

### Notes
- This version requires NetBox 3.7.8 or later


## [0.3.0] - 2025-03-03

### Added
- Mux device support for mapping wavelengths to multiplexer ports
- Enhanced validation for wavelength reservations and device assignments
- Comprehensive filtering capabilities for optical objects

### Changed
- Improved wavelength object model
- Updated naming conventions for better consistency
- Added name field to support better identification

### Fixed
- Wavelength status serialization
- Various bug fixes after initial demos and feedback

## [0.2.0] - 2025-02-27

### Added
- Optical Grid Types: Define wavelength grid templates (DWDM, CWDM, FlexGrid)
- Optical Grid Instances: Create grid instances from templates
- Wavelength Management: Track individual wavelengths with availability status
- Optical Spans: Model optical fiber connections between sites
- Optical Connections: Map interfaces to wavelengths on spans
- Full REST API support for automation
- Comprehensive validation

### Changed
- Multiple fixes after demo feedback
- Updated tests for better coverage

## [0.1.0] - 2025-02-18

### Added
- Initial development release
- Basic optical connection modeling
- Core plugin infrastructure

