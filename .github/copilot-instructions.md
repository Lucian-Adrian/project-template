## Code Conventions

### Code Quality Criteria
- **KISS**: Keep it simple, stupid
- **DRY**: Don't repeat yourself
- **YAGNI**: You aren't gonna need it
- **SOLID**: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion
- **Max 100 lines per file** - split large files into smaller modules, exceptions for frontend files
- **Separation of concerns**: Each module handles one concern
- **Modular design**: Reusable, testable, scalable components

### File Organization
- Separate each major component/concern per file
- Large code → split into smaller components, import in main file
- Document structure changes in `docs/file-structure.md`

### Code Standards
- Clean, readable code with clear reasoning
- Proper error handling and logging
- Security best practices
- Performance considerations
- Handle edge cases
- Future-proof: changes don't require huge refactoring
- Consistent coding style throughout